from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from gestion_groupes import auth_views

def home_redirect(request):
    """Redirection intelligente selon l'état de connexion"""
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    else:
        return redirect('/login/')


urlpatterns = [
    path('admin/', admin.site.urls),


    path('', home_redirect, name='home'),

    # URLs d'authentification avec imports corrects
    path('login/', auth_views.user_login, name='login'),
    path('logout/', auth_views.user_logout, name='user_logout'),
    path('profile/', auth_views.user_profile, name='user_profile'),
    path('change-password/', auth_views.change_password, name='change_password'),
    
    # URLs des applications
    #path('', include('suivi_conducteurs.urls')),
    #path('groupes/', include('gestion_groupes.urls')),
    # Dashboard protégé
    path('dashboard/', include('suivi_conducteurs.urls')),
    path('groupes/', include('gestion_groupes.urls')),    

    path('api/dashboard-stats/', auth_views.dashboard_stats, name='dashboard_stats'),
]

# Servir les fichiers statiques en développement
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    if hasattr(settings, 'MEDIA_URL') and hasattr(settings, 'MEDIA_ROOT'):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Gestionnaires d'erreurs personnalisés
handler403 = auth_views.access_denied
handler404 = auth_views.page_not_found
handler500 = auth_views.server_error
