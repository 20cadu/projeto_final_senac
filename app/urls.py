from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from . import views
from .views import ProdutoDeleteView, MainView, SignUpView, HomeView, IntroView, ProdutosView, CarrinhoConfirmarView, CarrinhoAddView, CarrinhoListView, CarrinhoFinalizarView

urlpatterns = [
    path('', IntroView.as_view(), name='intro'),
    path('base', HomeView.as_view(),name='home'),
    path('main', MainView.as_view(), name='main' ),
    path('produtos', ProdutosView.as_view(), name='produtos'),
    path('produtos/delete/<int:pk>/', ProdutoDeleteView.as_view(), name='delete_produto'),
    path('carrinho/confirmar/', CarrinhoConfirmarView.as_view(), name='carrinho_confirmar'),
    path('carrinho/add/<int:produto_id>/', CarrinhoAddView.as_view(), name='carrinho_add'),
    path('carrinho/list/', CarrinhoListView.as_view(), name='carrinho_list'),
    path('carrinho/finalizar/', CarrinhoFinalizarView.as_view(), name='carrinho_finalizar'),
]

urlpatterns += [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='main'), name='logout'),
]
