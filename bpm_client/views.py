from django.shortcuts import render


def task_definition_flowchart(request, task_class_name):
    return render(request, 'flowchart/task-definition.html', {'task_class_name': task_class_name})


def task_flowchart(request, task_id):
    return render(request, 'flowchart/task.html', {'task_id': task_id})