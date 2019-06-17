from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from .forms import PledgeForm, ValidateForm
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from pledge.models import Pledge
from pledge.serializers import PledgeSerializer
import hashlib
import twitter
import urllib

def emailView(request):
    if request.method == 'GET':
        form = PledgeForm()
    else:
        form = PledgeForm(request.POST)
        if form.is_valid():
            subject = 'Confirm your strike pledge'
            username = form.cleaned_data['email']
            email = username + '@kp.org'
            hashed_email = hashlib.sha1(email.lower().encode()).hexdigest()
            validate_link = 'kaiserstrike[dot]org/validate/?u={u}&e={e}'.format(u=username,e=hashed_email)
            message = 'Hello!\n\nYou or your co-worker indicated you want Kaiser to remain a best place to work, and to receive care.\n\n'
            message += 'To finalize strike pledge, please copy-paste this link into your browser address bar:\n\n'
            message += '(IMPT: replace "[dot]" with "." -->)    ' + validate_link
            message += '\n\n\n\n\nFrom,\n\n'
            message += 'Your friends at kaiserstrike.org'
            try:
                Pledge.objects.get(email_hash=hashed_email)
                send_mail(subject, message, 'noreply <noreply@kaiserstrike.org>', [email], fail_silently=True)
            except Pledge.DoesNotExist:
                try:
                    send_mail(subject, message, 'noreply <noreply@kaiserstrike.org>', [email], fail_silently=True)
                except BadHeaderError:
                    return HttpResponse('Invalid header found.')
                except Exception:
                    print('')
                return redirect('success')
    return render(request, "email.html", {'form': form})

def successView(request):
	return render(request,"success.html")

def validateView(request):
    if request.method == 'GET':
        email_hash = request.GET['e']
        work_email = request.GET['u']+'@kp.org'
        form = ValidateForm(initial={'email_hash': email_hash, 'work_email': work_email})
    elif request.method == 'POST':
        form = ValidateForm(request.POST)
        if form.is_valid():
            email_hash = form.cleaned_data['email_hash']
            work_email = form.cleaned_data['work_email']
            if email_hash == hashlib.sha1(work_email.lower().encode()).hexdigest():
                union_member = form.cleaned_data['union_member']
                region = form.cleaned_data['kaiser_region']
                pers_email = form.cleaned_data['personal_email']
                tweet = form.cleaned_data['tweet']
                count = Pledge.objects.all().count()
                if tweet != '' and count > 1000:
                    api = twitter.Api(consumer_key=os.environ['consumer_key'],
								  consumer_secret=os.environ['consumer_secret'],
								  access_token_key=os.environ['access_token_key'],
								  access_token_secret=os.environ['access_token_secret'])
                    try:
                        api.PostUpdate(tweet[0:245] + '... #kaiserstrike @aboutKP @kpthrive')
                    except:
                        print('')
                try:
                    pledge = Pledge.objects.get(email_hash=email_hash)
                    pledge.union_member = union_member
                    pledge.region = region
                    pledge.pers_email = pers_email
                    pledge.message = tweet
                    pledge.save()
                except Pledge.DoesNotExist:
                    Pledge.objects.create(email_hash = email_hash,
                                      work_email = work_email,
                                      union_member = union_member,
									  region = region,
									  pers_email = pers_email,
                                      message = tweet)
                return redirect('confirm')
    return render(request, "contact.html", {'form': form})

def aboutView(request):
    return render(request, "about.html")

def faqView(request):
    return render(request, "faq.html")

def termsView(request):
    return render(request, "terms.html")

def privacyView(request):
    return render(request, "privacy.html")

def homeView(request):
    count = Pledge.objects.all().count
    if count < 1000:
        count = '< 1000'
    return render(request, "home.html", {'count': count})

def confirmView(request):
    return render(request, "confirmation.html")

def unionView(request):
    return render(request, "unions.html")
