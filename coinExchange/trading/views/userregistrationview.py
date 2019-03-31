from django.db.models import Q
from django.db import transaction
from django.contrib import messages
from django.shortcuts import render, redirect
from trading.controller.token import account_activation_token

from django.template.loader import render_to_string
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.sites.shortcuts import get_current_site

from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from django.core.mail import EmailMessage
from django.http import HttpResponse

from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.sites.shortcuts import get_current_site

from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import activate

from django.core.mail import EmailMessage
from django.http import HttpResponse

from trading.models import *
from django.contrib.auth.models import User
from trading.views.models.registration import SignUpForm

import logging,json

rlogger = logging.getLogger("site.registration")

def registration(request):
    if request.method == 'POST':
        activate('zh')
        form = SignUpForm(request.POST)

        if form.is_valid():

            # username = form.cleaned_data.get('username')
            # loginmanager.create_login(form, username)
            # raw_password = form.cleaned_data.get('password1')
            # user = authenticate(username=username, password=raw_password)
            # login(request, user)
            # return redirect('home')

            user = None
            with transaction.atomic():
                user = form.save(commit=False)
                user.is_active = False
                user.save()
                user_wallet = UserWallet.objects.select_for_update().filter(Q(user__isnull=True))[0]
                user_wallet.user = user
                user_wallet.save()

            rlogger.info('User created in db, but deactive') 

            current_site = get_current_site(request)

            mail_subject = '请激活您的美基金账户.'
            message = render_to_string('registration/user_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })

            to_email = form.cleaned_data.get('email')

            rlogger.info('Email to {0}'.format(to_email))

            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )

            email.send()
            messages.success(request, '您的注册激活链接已经发到您的注册邮箱{0}。请在三天内激活。'.format(to_email))
            return render(request, 'registration/registration_confirm.html')

    else:
        form = SignUpForm()
    return render(request, 'registration/register.html', {'form': form})

def activate_user_registration(request, uidb64, token):
    try:

        # Given uidb64 is a bytes object, so its string form is like b'MTY', we need to remove b and ' to make decoding works.
        uid = force_text(urlsafe_base64_decode(uidb64[2:-1]))

        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
        user = None
        rlogger.error('fail to activate user registration, uidb64: {0}, token: {1}, exception: {2}'.format(uidb64, token, e))

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('home')
        #return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
    else:
        return HttpResponse('Activation link is invalid!')
