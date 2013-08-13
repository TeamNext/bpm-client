from django.shortcuts import render

def task_definition_flow_chart(request, task_class_name):
    return render(request, 'flowchart_demo/auto_flow.html', {'task_class_name':task_class_name})