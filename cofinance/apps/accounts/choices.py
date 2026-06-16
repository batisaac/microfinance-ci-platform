from django.db import models


class Role(models.TextChoices):
    CLIENT = "client", "Client"
    AGENT = "agent", "Agent de terrain"
    ADMIN = "admin", "Administrateur"


class Region(models.TextChoices):
    ABIDJAN = "abidjan", "Abidjan"
    YAMOUSSOUKRO = "yamoussoukro", "Yamoussoukro"
    BOUAKE = "bouake", "Bouaké"
    DALOA = "daloa", "Daloa"
    KORHOGO = "korhogo", "Korhogo"
    SAN_PEDRO = "san_pedro", "San Pédro"
    GAGNOA = "gagnoa", "Gagnoa"
    MAN = "man", "Man"
    ODIENNE = "odienne", "Odienné"
    ABENGOUROU = "abengourou", "Abengourou"
