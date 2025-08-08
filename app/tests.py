from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, Client
from django.urls import reverse
from app.models import Produto, Usuario

class SistemaTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='cliente',
            password='senha@123',
            email='cliente@email.com'
        )
        self.staff = User.objects.create_user(
            username='admin',
            password='senha@123',
            is_staff=True
        )
        self.produto = Produto.objects.create(
            nome='Produto Teste',
            descricao='Descrição',
            preco=10.0,
            estoque=5
        )

    # --- AUTENTICAÇÃO ---
    def test_signup_cria_usuario(self):
        dados = {
            'username': 'novo',
            'email': 'novo@email.com',
            'password1': 'Senha@12345',
            'password2': 'Senha@12345',
            'nome': 'Novo Usuário',
            'telefone': '999999999',
            'cidade': 'Cidade'
        }
        resp = self.client.post(reverse('signup'), dados)
        self.assertIn(resp.status_code, (301, 302))
        self.assertTrue(User.objects.filter(username='novo').exists())
        self.assertTrue(Usuario.objects.filter(nome='Novo Usuário').exists())

    # --- PRODUTOS ---
    def test_produtos_get(self):
        self.client.login(username='cliente', password='senha@123')
        resp = self.client.get(reverse('produtos'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Produto Teste')

    def test_produtos_post_valido(self):
        self.client.login(username='cliente', password='senha@123')
        resp = self.client.post(reverse('produtos'), {
            'nome': 'Produto Novo',
            'descricao': 'Desc',
            'preco': 5.0,
            'estoque': 3
        })
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Produto.objects.filter(nome='Produto Novo').exists())

    def test_produtos_post_invalido(self):
        self.client.login(username='cliente', password='senha@123')
        resp = self.client.post(reverse('produtos'), {
            'nome': '',
            'descricao': '',
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn('errors', resp.json())

    def test_delete_produto_staff(self):
        self.client.login(username='admin', password='senha@123')
        resp = self.client.delete(reverse('delete_produto', args=[self.produto.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Produto.objects.filter(id=self.produto.id).exists())

    def test_delete_produto_dono(self):
        self.client.login(username='admin', password='senha@123')  # usuário staff
        resp = self.client.delete(reverse('delete_produto', args=[self.produto.id]))
        self.assertEqual(resp.status_code, 200)  # ou 302 se redirecionar após delete

    def test_delete_produto_sem_permissao(self):
        outro_user = User.objects.create_user(username='outro', password='senha@123')
        self.client.login(username='outro', password='senha@123')
        resp = self.client.delete(reverse('delete_produto', args=[self.produto.id]))
        self.assertEqual(resp.status_code, 403)

    def test_delete_produto_inexistente(self):
        self.client.login(username='admin', password='senha@123')
        resp = self.client.delete(reverse('delete_produto', args=[999]))
        self.assertEqual(resp.status_code, 404)

    # --- CARRINHO ---
    def test_carrinho_add_e_list(self):
        self.client.login(username='cliente', password='senha@123')
        resp = self.client.post(reverse('carrinho_add', args=[self.produto.id]))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse('carrinho_list'))
        self.assertEqual(len(resp.json()['itens']), 1)

    def test_carrinho_confirmar_requer_login(self):
        resp = self.client.get(reverse('carrinho_confirmar'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)

    def test_carrinho_confirmar_logado(self):
        self.client.login(username='cliente', password='senha@123')
        self.client.post(reverse('carrinho_add', args=[self.produto.id]))
        resp = self.client.get(reverse('carrinho_confirmar'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Produto Teste')

    def test_carrinho_finalizar_sucesso(self):
        self.client.login(username='cliente', password='senha@123')
        self.client.post(reverse('carrinho_add', args=[self.produto.id]))
        resp = self.client.post(reverse('carrinho_finalizar'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['success'])
        self.assertEqual(len(mail.outbox), 1)  # E-mail enviado

    def test_carrinho_finalizar_vazio(self):
        self.client.login(username='cliente', password='senha@123')
        resp = self.client.post(reverse('carrinho_finalizar'))
        self.assertEqual(resp.status_code, 400)

    def test_carrinho_finalizar_sem_email(self):
        self.user.email = ''
        self.user.save()
        self.client.login(username='cliente', password='senha@123')
        self.client.post(reverse('carrinho_add', args=[self.produto.id]))
        resp = self.client.post(reverse('carrinho_finalizar'))
        self.assertEqual(resp.status_code, 400)


