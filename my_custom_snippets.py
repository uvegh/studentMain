
notice = ModelNotifications.objects.create(student=student, 
supervisor=supervisor, notice=f"project updated on <a href=\'/project/upload/{pk}\'>view</a>",
        supervisor_read=True
        )




notice = ModelNotifications.objects.filter(student=student, supervisor=supervisor, student_read=student_read)