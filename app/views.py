import cloudinary.uploader
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, CreateView, UpdateView

from app.forms import SignUpForm, ProdutoForm
from app.models import Usuario, Produto


# Create your views here.

class IntroView(TemplateView):
    template_name = 'app/intro.html'

class HomeView(TemplateView):
    template_name = 'app/base.html'

class MainView(TemplateView):
    def get(self, request):
        form = ProdutoForm()
        produtos = Produto.objects.all()
        return render(request, 'app/main.html', {
            'form': form,
            'produtos': produtos
        })


class SignUpView(CreateView):
    model = User
    form_class = SignUpForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('main')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        is_staff = self.request.POST.get('is_staff') == 'on'
        self.object.is_staff = is_staff
        self.object.save()

        Usuario.objects.create(
            user=self.object,
            nome=form.cleaned_data.get('nome'),
            telefone=form.cleaned_data.get('telefone'),
            cidade=form.cleaned_data.get('cidade'),
        )

        login(self.request, self.object)

        return redirect(self.success_url)

class ProdutosView(View):
    def get(self, request):
        form = ProdutoForm()
        produtos = Produto.objects.all()
        return render(request, 'app/produtos.html', {
            'form': form,
            'produtos': produtos
        })

    def post(self, request, *args, **kwargs):
        form = ProdutoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('main')  # Redireciona para a URL nomeada 'main'
        return render(request, 'app/produtos.html', {
            'form': form
        })

class ProdutoEditView(View):
    def get(self, request, pk):
        produto = get_object_or_404(Produto, pk=pk)
        form = ProdutoForm(instance=produto)
        return render(request, 'app/produto_edit.html', {'form': form, 'produto': produto})

    def post(self, request, pk):
        produto = get_object_or_404(Produto, pk=pk)
        form = ProdutoForm(request.POST, request.FILES, instance=produto)
        if form.is_valid():
            nova_imagem = form.cleaned_data.get('imagem')
            if nova_imagem:
                if produto.imagem:
                    try:
                        cloudinary.uploader.destroy(produto.imagem.public_id)
                    except Exception as e:
                        print("Erro ao deletar imagem antiga:", e)
            form.save()
            return redirect('main')
        return render(request, 'app/produto_edit.html', {'form': form, 'produto': produto})

class ProdutoDeleteView(View):
    def delete(self, request, pk):
        try:
            produto = Produto.objects.get(pk=pk)
            # Verifica se o usuário é staff ou dono do produto
            if request.user.is_staff:
                produto.delete()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'error': 'Permissão negada'}, status=403)
        except Produto.DoesNotExist:
            return JsonResponse({'error': 'Produto não encontrado'}, status=404)

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() == 'delete':
            return self.delete(request, *args, **kwargs)
        return HttpResponseNotAllowed(['DELETE'])

class CarrinhoConfirmarView(LoginRequiredMixin, View):
    login_url = '/login/'  # ou o caminho que usar para login
    redirect_field_name = 'next'

    def get(self, request):
        carrinho = request.session.get('carrinho', [])
        produtos = Produto.objects.filter(id__in=carrinho)
        total = sum([p.preco for p in produtos])
        return render(request, 'app/confirmacao.html', {'produtos': produtos, 'total': total})

class CarrinhoAddView(View):
    def post(self, request, produto_id):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        carrinho = request.session.get('carrinho', [])
        produto_id = int(produto_id)
        if produto_id not in carrinho:
            carrinho.append(produto_id)
            request.session['carrinho'] = carrinho
        return JsonResponse({'message': 'Produto adicionado ao carrinho!'})

class CarrinhoListView(View):
    def get(self, request):
        carrinho = request.session.get('carrinho', [])
        produtos = Produto.objects.filter(id__in=carrinho)
        itens = [{'nome': p.nome, 'preco': p.preco} for p in produtos]
        return JsonResponse({'itens': itens})

class CarrinhoFinalizarView(View):
    def post(self, request):
        try:
            user = request.user
            email = user.email
            produtos_ids = request.session.get('carrinho', [])
            produtos = Produto.objects.filter(id__in=produtos_ids)
            total = sum([p.preco for p in produtos])
            lista_produtos = "\n".join([f"{p.nome} - R${p.preco}" for p in produtos])

            if not produtos:
                return JsonResponse({'success': False, 'message': 'Carrinho vazio.'}, status=400)

            if not email:
                return JsonResponse({'success': False, 'message': 'Usuário sem e-mail cadastrado.'}, status=400)

            send_mail(
                'Confirmação de Compra - PromoMarket',
                f'Olá {user.username},\n\nSua compra foi confirmada!\n\nProdutos:\n{lista_produtos}\n\nTotal: R${total}\n\nObrigado por comprar conosco!',
                'settings.EMAIL_HOST_USER',  # Remetente
                [email],
                fail_silently=False,
            )

            request.session['carrinho'] = []
            return JsonResponse({'success': True, 'message': 'Compra finalizada e e-mail enviado!'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
