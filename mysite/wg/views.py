from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from .models import Template
import json

def cons(request):
    return render(request, 'wg/cons.html', {})

def save_template(request):
    result = {'flg':False}
    template = Template(name=request.GET["name"], cons=request.GET["cons"], count=request.GET["count"])
    template.save()
    result['flg'] = True
    return HttpResponse(json.dumps(result))

def get_template(request):
    result = {'flg':False}
    res_template = []
    templates = Template.objects.filter(del_flg=False)
    for template in templates:
        res_template.append({
            "id": template.id,
            "name": template.name,
            "constitution": json.loads(template.cons),
            "count": template.count,
        })
    result['template'] = json.dumps(res_template)
    result['flg'] = True
    return HttpResponse(json.dumps(result))

def del_template(request):
    result = {'flg':False}
    templates = Template.objects.get(pk=request.GET["id"])
    templates.del_flg = True
    templates.save()
    result['flg'] = True
    return HttpResponse(json.dumps(result))
