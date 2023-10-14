from django.contrib import admin

# Register your models here.
from django.db import models
from import_export.admin import ImportExportModelAdmin


class ImportExportAdmin(ImportExportModelAdmin, admin.ModelAdmin):

    def __init__(self, model, admin_site):
        self.list_display = [field.name for field in model._meta.fields]
        self.list_filter = [field.name for field in model._meta.fields]
        self.search_fields = [field.name for field in model._meta.fields
                              if field.name != 'id' and
                              not isinstance(field, models.ForeignKey) and
                              not isinstance(field, models.ManyToManyField) and
                              not isinstance(field, models.OneToOneField)
                              ]
        super(ImportExportAdmin, self).__init__(model, admin_site)


admin_class = type('AdminClass', (ImportExportAdmin, admin.ModelAdmin), {})


