from datetime import datetime
from email.policy import default
from random import random
from django.core.management.base import BaseCommand
from django.apps import apps
from django.conf import settings

from .seed_data import *
import random
from django.db import IntegrityError
import pdb
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Create seed data for all models'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exception_count_limit = 5
        self.total_instances = 1
        self.restricted_datatypes = [
            models.fields.related.ManyToManyField, 
            models.fields.reverse_related.ManyToOneRel, 
            models.fields.reverse_related.ManyToManyRel, 
            models.fields.reverse_related.OneToOneRel, 
            models.fields.BigAutoField, 
            GenericRelation, 
            models.fields.SlugField, 
            models.fields.UUIDField,
            models.fields.files.FileField,
            models.fields.files.ImageField
        ]
        self.apps_list = self.get_all_installed_apps()
        self.foreign_key_models = []

    def handle(self, *args, **kwargs):
        for each_app in self.apps_list:
            model_list = self.get_all_models(app_name = each_app)
            for each_model in model_list:
                self.exception_count = 0
                fields, datatypes = self.get_fields_and_datatypes(each_model)
                if models.ManyToManyField in datatypes or GenericForeignKey in datatypes:
                    continue
                if models.FileField in datatypes or models.ImageField in datatypes:
                    continue
                if models.fields.related.ForeignKey in datatypes or models.fields.related.OneToOneField in datatypes:
                    self.foreign_key_models.append(each_model)
                else:
                    self.get_data_and_populate_model(each_model, fields)
        self.populate_foreign_key_models()

    def get_all_models(self, app_name = None):
        if app_name:
            return apps.get_app_config(app_name).get_models()
        else:
            app_names = None
            models = []
            for app in app_names:
                app_models = apps.get_app_config(app).get_models()
                models.extend(app_models)
            return models

    def get_all_installed_apps(self):
        apps_list = [each_app for each_app in settings.INSTALLED_APPS if not each_app.startswith("django.")]
        return apps_list

    def get_relevant_data(self, field):
        name = field.name
        data_type = type(field)
        empty_strings_allowed = field.empty_strings_allowed
        is_null = field.null
        random_data = None
        if data_type == models.fields.CharField:
            default = field._get_default()
            if default:
                random_data = default
            else:
                max_length = field.max_length
                random_data = self.get_relevant_string_data(name, max_length)
        elif data_type == models.fields.TextField:
            random_data = random.choice(LONG_TEXT)
        elif data_type in [models.fields.IntegerField, models.fields.PositiveIntegerField]:
            random_data = random.choice(list(range(1,11)))
        elif data_type == models.fields.FloatField:
            random_data = random.choice(list(range(1.0, 11.0)))
        elif data_type == models.fields.related.ForeignKey or data_type == models.fields.related.OneToOneField:
            parent_model = field.related_model
            total_count_of_parent_model = parent_model.objects.count()
            try:
                random_data = parent_model.objects.get(id = random.choice(list(range(1, total_count_of_parent_model+1))))
            except parent_model.DoesNotExist:
                raise ObjectDoesNotExist
            except IndexError:
                random_data = None
        elif data_type == models.fields.BooleanField:
            random_data = random.choice(BOOLEAN)
        elif data_type == models.fields.DateField:
            random_data = random.choice(DATES)
        elif data_type == models.fields.EmailField:
            random_data = random.choice(EMAIL)
        elif data_type == models.fields.DateTimeField:
            random_data = datetime.now()
        elif data_type == models.fields.json.JSONField:
            random_data = {"key": "value"}
        else:
            if is_null and empty_strings_allowed:
                random_data = None
        if isinstance(random_data, ContentType):
            pass
        return random_data

    def populate_data(self, model, data):
        try:
            _ = model.objects.create(**data)
        except IntegrityError as e:
            self.exception_count += 1
            if self.exception_count == self.exception_count_limit:
                return
            fields, _ = self.get_fields_and_datatypes(model)
            data = {each.name:self.get_relevant_data(each) for each in fields}
            self.populate_data(model, data)

    def clean_variable_name(self, var_name):
        var_name = str(var_name).rsplit(".", 1)[1]
        return var_name

    def get_relevant_string_data(self, var_name, max_length):
        value = None
        if "first" in var_name:
            value = random.choice(FIRST_NAME)
        elif "last" in var_name:
            value = random.choice(LAST_NAME)
        elif "address" in var_name:
            value = random.choice(ADDRESS)
        elif "contact" in var_name or "phone" in var_name:
            value = random.choice(CONTACT_NUMBER)
        else:
            value = random.choice(WORDS)
        return value[:max_length-1]

    def get_data_and_populate_model(self, model, fields):
        status = True
        for _ in range(self.total_instances):
            try:
                data = {each.name:self.get_relevant_data(each) for each in fields}
                self.populate_data(model, data)
            except ObjectDoesNotExist:
                status = False
                return status
        return status

    def get_fields_and_datatypes(self, model):
        fields = model._meta.get_fields()
        fields = list(filter(lambda x: type(x) not in self.restricted_datatypes, fields))
        datatypes = [type(each) for each in fields]
        return (fields, datatypes)

    def populate_foreign_key_models(self):
        temp_fk_models = self.foreign_key_models
        while True:
            for index, each_model in enumerate(temp_fk_models):
                try:
                    fields, _ = self.get_fields_and_datatypes(each_model)
                    status = self.get_data_and_populate_model(each_model, fields)
                    if status:
                        temp_fk_models.pop(index)
                    else:
                        continue
                except Exception as e:
                    self.exception_count += 1
                    if self.exception_count == self.exception_count_limit:
                        return
            if not temp_fk_models:
                break
