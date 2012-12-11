from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from corehq.apps.domain.decorators import require_superuser
from django.views.decorators.http import require_POST
from corehq.apps.domain.models import Domain
from corehq.apps.commtrack.management.commands import bootstrap_psi
import bulk
import json

@require_superuser
def bootstrap(request, domain):
    if request.method == "POST":
        D = Domain.get_by_name(domain)
        if D.commtrack_enabled:
            return HttpResponse('already configured', 'text/plain')
        else:
            bootstrap_psi.one_time_setup(D)
            return HttpResponse('set up successfully', 'text/plain')

    return HttpResponse('<form method="post" action=""><button type="submit">Bootstrap Commtrack domain</button></form>')

@require_superuser
def location_import(request, domain):
    if request.method == "POST":
        messages = list(bulk.import_locations(domain, request.FILES['locs']))
        return HttpResponse('results:\n\n' + '\n'.join(messages), 'text/plain')

    return HttpResponse("""
<form method="post" action="" enctype="multipart/form-data">
  <div><input type="file" name="locs" /></div>
  <div><button type="submit">Import locations</button></div>
</form>
""")

@require_superuser
def historical_import(request, domain):
    if request.method == "POST":
        try:
            result = bulk.import_stock_reports(domain, request.FILES['history'])
            resp = HttpResponse(result, 'text/csv')
            resp['Content-Disposition'] = 'attachment; filename="import_results.csv"'
            return resp
        except Exception, e:
            return HttpResponse(str(e), 'text/plain')


    return HttpResponse("""
<form method="post" action="" enctype="multipart/form-data">
  <div><input type="file" name="history" /></div>
  <div><button type="submit">Import historical stock reports</button></div>
</form>
""")
