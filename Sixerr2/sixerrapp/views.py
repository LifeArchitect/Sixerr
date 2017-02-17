from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Gig, Profile, Purchase, Review
from .forms import GigForm
import braintree

braintree.Configuration.configure(braintree.Environment.Sandbox,
                                  merchant_id="x8bjst3dq2wqx36d",
                                  public_key="4tr9rj2gjyhf3jsr",
                                  private_key="bc948fcddd435d9b9f10691f3eb14d5a")

# Create your views here.
def home(request):
    gigs = Gig.objects.filter(status=True)
    return render(request, 'home.html', {"gigs": gigs})

def gigDetails(request, id):
    try:
        gig = Gig.objects.get(id=id)
    except Gig.DoesNotExist:
        return redirect('/')

    if request.user.is_anonymous():
        show_post_review = False
    else:
        show_post_review = Purchase.objects.filter(gig=gig, buyer=request.user).count() > 0

    reviews = Review.objects.filter(gig=gig)
    def client_token():
        return braintree.ClientToken.generate()

    return render(request, 'gigDetails.html', {"show_post_review": show_post_review, "reviews": reviews, "gig": gig, "client_token": client_token})

@login_required(login_url="/")
def create_gig(request):
    error = ''
    if request.method == 'POST':
        gig_form = GigForm(request.POST, request.FILES)
        if gig_form.is_valid():
            gig = gig_form.save(commit=False)
            gig.user = request.user
            gig.save()
            return redirect('my_gigs')
        else:
            error = "Data is not valid"

    gig_form = GigForm()
    return render(request, 'create_gig.html', {"error": error})

@login_required(login_url="/")
def edit_gig(request, id):
    try:
        gig = Gig.objects.get(id=id, user=request.user)
        error = ''
        if request.method == 'POST':
            gig_form = GigForm(request.POST, request.FILES, instance=gig)
            if gig_form.is_valid():
                gig.save()
                return redirect('my_gigs')
            else:
                error = "Data is not valid"
        return render(request, 'edit_gig.html', {"gig": gig, "error": error})
    except Gig.DoesNotExist:
        return redirect('/')

@login_required(login_url="/")
def my_gigs(request):
    gigs = Gig.objects.filter(user=request.user)
    return render(request, 'my_gigs.html', {"gigs": gigs})

@login_required(login_url="/")
def profile(request, username):
    if request.method == 'POST':
        profile = Profile.objects.get(user=request.user)
        profile.about = request.POST.get('about', False)
        profile.slogan = request.POST.get('slogan', False)
        profile.save()
    try:
        profile = Profile.objects.get(user__username=username)
    except Profile.DoesNotExist:
        return redirect('/')

    gigs = Gig.objects.filter(user=profile.user, status=True)
    return render(request, 'profile.html', {"profile": profile, "gigs": gigs})

@login_required(login_url="/")
def create_purchase(request):
    if request.method == 'POST':
        try:
            gig = Gig.objects.get(id = request.POST['gig_id'])
        except Gig.DoesNotExist:
            return redirect('/')

        nonce = request.POST.get('payment_method_nonce', False)
        result = braintree.Transaction.sale({
           "amount": gig.price, "payment_method_nonce": nonce
        })

        if result.is_success:
            Purchase.objects.create(gig=gig, buyer=request.user)

    return redirect('/')

@login_required(login_url="/")
def my_sold(request):
        purchases = Purchase.objects.filter(buyer=request.user)
        return render(request, 'my_purchases.html', {"purchases": purchases})

@login_required(login_url="/")
def my_purchases(request):
    purchases = Purchase.objects.filter(gig__user=request.user)
    return render(request, 'my_purchases.html', {"purchases": purchases})

def category(request, link):
    categories = {
      "graphic-design": "GD",
      "digital-marketing": "DM",
      "video-animation": "VA",
      "music-audio": "MA",
      "programming-tech": "PT",
    }
    try:
        gigs = Gig.objects.filter(category=categories[link])
        return render(request, 'home.html', {"gigs": gigs})
    except KeyError:
        return redirect('home')

def search(request):
    gigs = Gig.objects.filter(title__contains=request.GET['title'])
    return render(request, 'home.html', {"gigs": gigs})
