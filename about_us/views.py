from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Feedback

def about_us(request):
    if request.method == 'POST':
        name = request.POST.get('name', 'Anonymous')
        feedback_text = request.POST.get('feedback')
        rating = request.POST.get('rating', '0')
        
        if feedback_text:  # Ensure feedback_text is not empty
            feedback = Feedback(name=name, feedback=feedback_text, rating=rating)
            feedback.save()
            messages.success(request, 'Thank you for your feedback!')
        else:
            messages.warning(request, 'Oops!!! Feedback is not saved!')
        return redirect('about_us')
    
    return render(request, 'about_us/about_us.html')
