from django.contrib.auth.models import User
from django.db import models

class Usuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    cidade = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username

class Produto(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.CharField(max_length=500)
    preco = models.IntegerField()
    estoque = models.IntegerField()
    imagem_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.nome