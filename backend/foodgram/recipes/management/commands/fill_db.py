import json

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        with open("data/ingredients.json") as f:
            data_list = json.load(f)

        for data in data_list:
            Ingredient.objects.all().delete
            Ingredient.objects.get_or_create(
                name=data["name"], measurement_unit=data["measurement_unit"]
            )
        print("added fixtures")
