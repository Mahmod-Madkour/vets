### account/view.py

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import  login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from .forms import *
from .models import *

####################################################################################################
####################################################################################################
# Sign Up
def sign_up(request):
    if request.user.is_authenticated:
        return redirect('post_home')
    else:
        form = RegisterForm()
        
        if request.method == 'POST':
            form = RegisterForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.username = user.username.lower()
                user.save()
                
                # Create Profile account for new user
                Profile.objects.create(user=user, first_name=user.first_name, last_name=user.last_name)                
                return redirect('login')
            else:
                messages.error(request, 'Please correct the error below.')
        context = {
            'form': form,
        }
        return render(request, 'auth/register.html', context)

# Sign In
def sign_in(request):
    if request.user.is_authenticated:
        return redirect('post_home')
    else:
        form = LoginForm()
        if request.method == 'POST':
            form = LoginForm(request.POST) 
            if form.is_valid():
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                user = authenticate(request, username=username, password=password)
                if user:
                    login(request, user)
                    return redirect('post_home')
                else:
                    # If authentication fails or form is invalid, display error message
                    messages.error(request, 'Username or Password is incorrect !')
        context = {
            'form': form,
        }
        return render(request, 'auth/login.html', context)

# Profile
@login_required(login_url='login')
def user_profile(request):
    profile = Profile.objects.filter(user= request.user).first()
    context = {
        'profile': profile,
        }
    return render(request, 'profile/profile.html', context=context)

# Profile For Everyone
@login_required(login_url='login')
def user_profile_everyone(request, pk_user):
    profile = Profile.objects.filter(user= pk_user).first()
    context = {
        'profile': profile,
        }
    return render(request, 'profile/profile_everyone.html', context=context)

# Update Profile
@login_required(login_url='login')
def profile_update(request):
    profile = request.user.profile
    form = ProfileEditForm(instance=profile)
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            pro = form.save()
            pro.save()

            # Update first_name, first_name in User
            User.objects.filter(username= profile).update(first_name=pro.first_name, last_name=pro.last_name)
            return redirect('user_profile')
        else:
            messages.error(request, 'Please correct the error below.')
    context = {
        'profile': profile,
        'form': form,
    }
    return render(request, 'profile/profile_update.html', context=context)

# Update Password
@login_required(login_url='login')
def update_password(request):
    user = request.user
    password_form = UpdatePasswordForm(user)
    if request.method == 'POST':
        password_form = UpdatePasswordForm(user, request.POST)
        if password_form.is_valid():
            password_form.save()
            UpdatePasswordForm(request, user)
            update_session_auth_hash(request, user)  # Important for security
            return redirect('user_profile')
        else:
            messages.error(request, 'Please correct the error below !')
    context = {
        'password_form': password_form,
    }
    return render(request, 'profile/update_password.html', context=context)

# Sign Out
@login_required(login_url='login')
def sign_out(request):
    logout(request)
    return redirect('login')

####################################################################################################
####################################################################################################
### Post Page
@login_required(login_url='login')
def post_home(request):
    if request.method == "GET":
        user = request.user
        posts = Post.objects.all().order_by("-created_on")
        likes = PostLikes.objects.filter(user=user)

        # Check User is Like
        combined_data = {}                  # Assuming posts and likes are lists or querysets
        for post in posts:                  # Initialize combined_data with 'unlike' for all posts
            combined_data[post] = 'unlike'
        for like in likes:                  # Update combined_data based on likes
            if like.post in combined_data:
                combined_data[like.post] = 'like'

        post_form = PostForm()
        context = {
            'user': user,
            'combined_data': combined_data,
            'post_form': post_form,
        }
        return render(request, "post/home.html", context)

    # Create a New Post
    if request.method == "POST":
        post_form = PostForm(request.POST)
        if post_form.is_valid():
            post = Post(
                user= request.user,
                body= post_form.cleaned_data["body"],
            )
            post.save()
            return redirect('/')

### Like of Post
@login_required(login_url='login')
def like_post(request, pk_post):
    post = Post.objects.filter(pk=pk_post).first()

    # Check if the user has already liked the post
    if PostLikes.objects.filter(user=request.user, post=post).exists():
        # Unlike the post
        PostLikes.objects.filter(user=request.user, post=post).delete()
        post.post_likes_count -= 1
    else:
        # Like the post
        PostLikes.objects.create(user=request.user, post=post)
        post.post_likes_count += 1
    post.save()
    return redirect('/')

### Num of Likes For Post
@login_required(login_url='login')
def all_likes_post(request, pk_post):
    post = Post.objects.get(id=pk_post)
    post_likes = PostLikes.objects.filter(post=pk_post)
    context = {
        'post': post,
        'post_likes': post_likes,
        }
    return render(request, 'post/post_likes.html', context)

### Update Post
@login_required(login_url='login')
def update_post(request, pk_post):
    if request.method == "GET":
        post = Post.objects.get(pk=pk_post)
        update_form = UpdateForm(instance=post)
        context = {
            'post': post,
            "update_form": update_form,
            }
        return render(request, 'post/update_post.html', context)
    
    if request.method == "POST":
        update_form = UpdateForm(request.POST, instance=post)
        if update_form.is_valid():
            update_form.save()
            return redirect('/')
    

### Delete Post
@login_required(login_url='login')
def delete_post(request, pk_post):
    post = Post.objects.filter(pk=pk_post)

    if request.method == 'GET' and post:
        return render(request, 'post/delete_post.html')
    
    if request.method == 'GET' and not post:
        return redirect('/')
    
    if request.method == 'POST' and post:
        post.delete()
        return redirect('/')

####################################################################################################

### Detail Of Post & Add Comment
@login_required(login_url='login')
def post_detail(request, pk_post):
    if request.method == "GET":
        user = request.user
        post = Post.objects.get(pk=pk_post)
        comments = Comment.objects.filter(post=post).order_by("-created_on")
        likes = CommentLikes.objects.filter(user=user)

        # Check User is Like
        combined_data = {}                      # Assuming posts and likes are lists or querysets
        for comment in comments:                # Initialize combined_data with 'unlike' for all posts
            combined_data[comment] = 'unlike'
        for like in likes:                      # Update combined_data based on likes
            if like.comment in combined_data:
                combined_data[like.comment] = 'like'

        comment_form = CommentForm()
        context = {
            'user': user,
            "post": post,
            "combined_data": combined_data,
            "comment_form": comment_form,
        }
        return render(request, "post/detail_post.html", context)
    
    if request.method == "POST":
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = Comment(
                body= comment_form.cleaned_data["body"],
                post= Post.objects.get(pk=pk_post),
                user= request.user,
            )
            comment.save()
            return redirect(reverse('post_detail', kwargs={'pk_post': pk_post}))

### Like of Comment
@login_required(login_url='login')
def like_comment(request, pk_post, pk_comment):
    comment = Comment.objects.get(pk=pk_comment)

    # Check if the user has already liked the post
    if CommentLikes.objects.filter(user=request.user, comment=comment).exists():
        # Unlike the post
        CommentLikes.objects.filter(user=request.user, comment=comment).delete()
        comment.comment_likes_count -= 1
    else:
        # Like the post
        CommentLikes.objects.create(user=request.user, comment=comment)
        comment.comment_likes_count += 1
    comment.save()
    
    return redirect(reverse('post_detail', kwargs={'pk_post': pk_post}))

### Update Comment
@login_required(login_url='login')
def update_comment(request, pk_post, pk_comment):
    if request.method == "GET":
        comment = Comment.objects.get(pk=pk_comment)
        update_form = UpdateForm(instance=comment)
        context = {
            'comment': comment,
            "update_form": update_form,
        }
        return render(request, 'post/update_comment.html', context)

    if request.method == "POST":
        update_form = UpdateForm(request.POST, instance=comment)
        if update_form.is_valid():
            update_form.save()
        return redirect(reverse('post_detail', kwargs={'pk_post': pk_post}))
    

### Delete Comment
@login_required(login_url='login')
def delete_comment(request, pk_post, pk_comment):
    comment = Comment.objects.filter(pk=pk_comment)
    
    if request.method == 'GET' and comment:
        return  render(request, 'post/delete_comment.html')

    if request.method == 'GET' and not comment:
        return redirect(reverse('post_home', kwargs={}))
    
    if request.method == 'POST' and comment:
        comment.delete()
        return redirect(reverse('post_detail', kwargs={'pk_post': pk_post}))

####################################################################################################

### Detail Of Comment & Add Replay
@login_required(login_url='login')
def comment_detail(request, pk_post, pk_comment):
    if request.method == "GET":
        user = request.user
        post = Post.objects.get(pk=pk_post)
        comment = Comment.objects.get(pk=pk_comment)
        replies = Replay.objects.filter(comment=comment).order_by("-created_on")
        likes = ReplayLikes.objects.filter(user=user)

        # Check User is Like
        combined_data = {}                          # Assuming posts and likes are lists or querysets
        for replay in replies:                      # Initialize combined_data with 'unlike' for all posts
            combined_data[replay] = 'unlike'
        for like in likes:                          # Update combined_data based on likes
            if like.replay in combined_data:
                combined_data[like.replay] = 'like'

        replay_form = ReplayForm()
        context = {
            'user': user,
            'post': post,
            "comment": comment,
            "combined_data": combined_data,
            "replay_form": replay_form,
        }
        return render(request, "post/detail_comment.html", context)

    if request.method == "POST":
        replay_form = ReplayForm(request.POST)
        if replay_form.is_valid():
            replay = Replay(
                body= replay_form.cleaned_data["body"],
                post=post,
                comment= comment,
                user= request.user,
            )
            replay.save()
            return redirect(reverse('comment_detail', kwargs={'pk_post': pk_post, 'pk_comment': pk_comment}))

### Like of Replay
@login_required(login_url='login')
def like_replay(request, pk_post, pk_comment, pk_replay):
    replay = Replay.objects.get(pk=pk_replay)

    # Check if the user has already liked the post
    if ReplayLikes.objects.filter(user=request.user, replay=replay).exists():
        # Unlike the post
        ReplayLikes.objects.filter(user=request.user, replay=replay).delete()
        replay.replay_likes_count -= 1
    else:
        # Like the post
        ReplayLikes.objects.create(user=request.user, replay=replay)
        replay.replay_likes_count += 1
    replay.save()
    
    return redirect(reverse('comment_detail', kwargs={'pk_post': pk_post, 'pk_comment': pk_comment}))

### Update Replay
@login_required(login_url='login')
def update_replay(request, pk_post, pk_comment, pk_replay):
    if request.method == "GET":
        replay = Replay.objects.get(pk=pk_replay)
        update_form = UpdateForm(instance=replay)
        context = {
            'replay': replay,
            "update_form": update_form,
        }
        return render(request, 'post/update_replay.html', context)

    if request.method == "POST":
        update_form = UpdateForm(request.POST, instance=replay)
        if update_form.is_valid():
            update_form.save()
            return redirect(reverse('comment_detail', kwargs={'pk_post': pk_post, 'pk_comment': pk_comment}))
    

### Delete Replay
@login_required(login_url='login')
def delete_replay(request, pk_post, pk_comment, pk_replay):
    replay = Replay.objects.filter(pk=pk_replay)

    if request.method == 'GET' and replay:
        return  render(request, 'post/delete_replay.html')

    if request.method == 'GET' and not replay:
        return redirect(reverse('post_detail', kwargs={'pk_post': pk_post}))
    
    if request.method == 'POST' and replay:
        replay.delete()
        return redirect(reverse('comment_detail', kwargs={'pk_post': pk_post, 'pk_comment': pk_comment}))

####################################################################################################
####################################################################################################
# All Questions
@login_required(login_url='login')
def question_home(request):
    if request.method == 'GET':
        questions = Question.objects.all().order_by("-created_on")
        context = {
            "questions": questions,
            }
        return render(request, "question/question.html", context)

# Ask New Question
@login_required(login_url='login')
def ask_question(request):
    if request.method == "GET":
        question_form = QuestionForm()
        context = {
            "question_form": question_form,
            }
        return render(request, "question/ask_question.html", context)
    
    if request.method == "POST":
        question_form = QuestionForm(request.POST)
        if question_form.is_valid():
            question = Question(
                user= request.user,
                title= question_form.cleaned_data["title"],
                body= question_form.cleaned_data["body"],
            )
            question.save()
            return redirect(reverse('question_home', kwargs={}))

# All Questions Same Status
@login_required(login_url='login')
def status_question(request, status):
    if request.method == "GET":
        questions = Question.objects.filter(status=status).order_by("-created_on")
        context = {
            "questions": questions,
            }
        return render(request, "question/status.html", context)

# All Detail of One Question
# Add New Answer & Vote Question & Display All Answers
@login_required(login_url='login')
def detail_question(request, pk_question):
    user = request.user
    question = Question.objects.get(pk=pk_question)

    if request.method == "GET":
        question_vote = QuestionVotes.objects.filter(user=user, question=question)
        answers = Answer.objects.filter(question=question).order_by("-created_on")
        answer_votes = AnswerVotes.objects.filter(user=user)

        # Check User is Vote
        combined_data = {}                          # Assuming posts and likes are lists or querysets
        for answer in answers:                      # Initialize combined_data with 'unvote' for all answers
            combined_data[answer] = 'unvote'
        for vote in answer_votes:                   # Update combined_data based on likes
            if vote.answer in combined_data:
                combined_data[vote.answer] = 'vote'

        answer_form = AnswerForm()
        context = {
            'question': question,
            'question_vote': question_vote,
            'combined_data': combined_data,
            'answer_form': answer_form,
            }
        return render(request, "question/detail_question.html", context)

    # Add New Answer
    if request.method == "POST":
        answer_form = AnswerForm(request.POST)
        if answer_form.is_valid():
            answer = Answer(
                body= answer_form.cleaned_data["body"],
                question= question,
                user= request.user,
            )
            answer.save()
            return redirect(reverse('detail_question', kwargs={'pk_question': pk_question}))

    # Vote Question
    if request.method == "POST":
        # Check if the user has already voted 
        if QuestionVotes.objects.filter(user=request.user, question=question).exists():
            # Un Vote
            QuestionVotes.objects.filter(user=request.user, question=question).delete()
            question.question_votes_count -= 1
        else:
            # Vote
            QuestionVotes.objects.create(user=request.user, question=question)
            question.question_votes_count += 1
        question.save()
        return redirect(reverse('detail_question', kwargs={'pk_question': pk_question}))

### Update Question
@login_required(login_url='login')
def update_question(request, pk_question):
    question = Question.objects.get(pk=pk_question)

    if request.method == "GET":
        update_form = UpdateQuestionForm(instance=question)
        context = {
            'question': question,
            "update_form": update_form,
        }
        return render(request, 'question/update_question.html', context)

    if request.method == "POST":
        updete_form = UpdateQuestionForm(request.POST, instance=question)
        if updete_form.is_valid():
            updete_form.save()
            return redirect(reverse('detail_question', kwargs={'pk_question': pk_question}))

### Delete Question
@login_required(login_url='login')
def delete_question(request, pk_question):
    question = Question.objects.filter(pk=pk_question)

    if request.method == 'GET' and question:
        return render(request, 'question/delete_question.html')

    if request.method == 'GET' and not question:
        return redirect(reverse('question_home'))

    if request.method == 'POST' and question:
        question.delete()
        return redirect(reverse('question_home'))
    
### Delete Answer
@login_required(login_url='login')
def delete_answer(request, pk_question, pk_answer):
    answer = Answer.objects.filter(pk=pk_answer)

    if request.method == 'GET' and answer:
        return render(request, 'question/delete_answer.html')
    
    if request.method == 'GET' and not answer:
        return redirect(reverse('question_home'))
    
    if request.method == 'POST' and answer:
        answer.delete()
        return redirect(reverse('detail_question', kwargs={'pk_question': pk_question }))

# Vote Answer
@login_required(login_url='login')
def vote_answer(request, pk_question, pk_answer):
    answer = Answer.objects.get(pk=pk_answer)
    
    # Check if the user has already voted 
    if AnswerVotes.objects.filter(user= request.user, answer=answer).exists():
        # Un Vote
        AnswerVotes.objects.filter(user= request.user, answer=answer).delete()
        answer.answer_votes_count -= 1
    else:
        # Vote
        AnswerVotes.objects.create(user= request.user, answer=answer)
        answer.answer_votes_count += 1
    answer.save()
    return redirect(reverse('detail_question', kwargs={'pk_question': pk_question }))

####################################################################################################
####################################################################################################
# All Diseases
@login_required(login_url='login')
def disease_home(request):
    diseases = Disease.objects.all().order_by("-created_on")
    context = {
        "diseases": diseases,
        }
    return render(request, "disease/disease.html", context)

# All Diseases Same Category
@login_required(login_url='login')
def category_disease(request, category):
    diseases = Disease.objects.filter(category=category).order_by("-created_on")
    context = {
        "diseases": diseases,
        }
    return render(request, "disease/category.html", context)

# Add New Disease
@login_required(login_url='login')
def add_disease(request):
    if request.method == "GET":
        disease_form = DiseaseForm()
        context = {
            "disease_form": disease_form,
            }
        return render(request, "disease/add_disease.html", context)
    
    if request.method == "POST":
        disease_form = DiseaseForm(request.POST, request.FILES)
        if disease_form.is_valid():
            disease = disease_form.save(commit=False)
            disease.user = request.user
            disease.save()
            return redirect(reverse('disease_home', kwargs={}))

# All Detail of One Disease
# Add New Answer & Vote Question & Display All Therapy
@login_required(login_url='login')
def detail_disease(request, pk_disease):
    disease = Disease.objects.get(pk=pk_disease)
    therapies = Therapy.objects.filter(disease=disease).order_by("-created_on")

    if request.method == "GET":
        therapy_form = TherapyForm()
        context = {
            'disease': disease,
            'therapies': therapies,
            'therapy_form': therapy_form,
            }
        return render(request, "disease/detail_disease.html", context)

    # Add New Therapy
    if request.method == "POST":
        therapy_form = TherapyForm(request.POST, request.FILES)
        if therapy_form.is_valid():
            therapy = therapy_form.save(commit=False)
            therapy.disease = disease
            therapy.user = request.user
            therapy.save()
            return redirect(reverse('detail_disease', kwargs={'pk_disease': pk_disease}))

### Delete Question
@login_required(login_url='login')
def delete_disease(request, pk_disease):
    disease = Disease.objects.filter(pk=pk_disease)

    if request.method == 'GET' and disease:
        return render(request, 'disease/delete_disease.html')

    if request.method == 'GET' and not disease:
        return redirect(reverse('disease_home'))

    if request.method == 'POST' and disease:
        disease.delete()
        return redirect(reverse('disease_home'))
    
### Delete Therapy
@login_required(login_url='login')
def delete_therapy(request, pk_disease, pk_therapy):
    therapy = Therapy.objects.filter(pk=pk_therapy)

    if request.method == 'GET' and therapy:
        return render(request, 'disease/delete_therapy.html')

    if request.method == 'GET' and not therapy:
        return redirect(reverse('detail_disease', kwargs={'pk_disease': pk_disease }))

    if request.method == 'POST' and therapy:
        therapy.delete()
        return redirect(reverse('detail_disease', kwargs={'pk_disease': pk_disease }))
    
### Delete Therapy Repaly
@login_required(login_url='login')
def delete_therapy_replay(request, pk_disease, pk_therapy, pk_replay):
    replay = ReplayTherapy.objects.filter(pk=pk_replay)

    if request.method == 'GET' and replay:
        return render(request, 'disease/delete_replay.html')

    if request.method == 'GET' and not replay:
        return redirect(reverse('detail_therapy', kwargs={'pk_disease': pk_disease, 'pk_therapy': pk_therapy}))

    if request.method == 'POST' and replay:
        replay.delete()
        return redirect(reverse('detail_therapy', kwargs={'pk_disease': pk_disease, 'pk_therapy': pk_therapy}))

### Detail Therapy
@login_required(login_url='login')
def detail_therapy(request, pk_disease, pk_therapy):
    user = request.user
    disease = Disease.objects.get(pk=pk_disease)
    therapy = Therapy.objects.get(pk=pk_therapy)
    
    if request.method == "GET":
        replies = ReplayTherapy.objects.filter(therapy=therapy).order_by("-created_on")
        replay_form = ReplayForm()
        context = {
            'user': user,
            'disease': disease,
            "therapy": therapy,
            "replies": replies,
            "replay_form": replay_form,
            }
        return render(request, "disease/detail_therapy.html", context)

    if request.method == "POST":
        replay_form = ReplayForm(request.POST)
        if replay_form.is_valid():
            replay = ReplayTherapy(
                body= replay_form.cleaned_data["body"],
                disease= disease,
                therapy= therapy,
                user= user,
            )
            replay.save()
            return redirect(reverse('detail_therapy', kwargs={'pk_disease': pk_disease, 'pk_therapy': pk_therapy}))
    

####################################################################################################
####################################################################################################
### Profile Post Page
@login_required(login_url='login')
def profile_posts(request):
    user = request.user
    profile = Profile.objects.filter(user= request.user).first()
    posts = Post.objects.filter(user=user).all().order_by("-created_on")
    found = 0

    if posts:
        found = found + 1
        # Calculate the count of comments for each post
        post_comments_count = {}
        for post in posts:
            count = Comment.objects.filter(post_id=post.id).count()
            post_comments_count[post.id] = count

        # Retrieve data from the database
        data = PostLikes.objects.all()
        likes = {}
        for item in data:
            likes[item.post_id] = item.user_id

        context = {
            'profile': profile,
            'found': found,
            'likes': likes,
            'user': user,
            'posts': posts,
            'post_comments_count': post_comments_count,
        }
        return render(request, "profile/profile_posts.html", context)
    else:
        context = {
            'profile': profile,
            'found': found,
            'user': user,
        }
        return render(request, "profile/profile_posts.html", context)


### Profile Question Page
@login_required(login_url='login')
def profile_questions(request):
    user = request.user
    profile = Profile.objects.filter(user= request.user).first()
    questions = Question.objects.filter(user=user).all().order_by("-created_on")
    found = 0

    if questions:
        found = found + 1
        # Calculate the count of answers for each question
        question_answers_count = {}
        for question in questions:
            count = Answer.objects.filter(question_id=question.id).count()
            question_answers_count[question.id] = count

        context = {
            'found': found,
            'profile': profile,
            "questions": questions,
            'question_answers_count': question_answers_count,
        }
    else:
        context = {
            'found': found,
            'profile': profile,
            'user': user,
            }
    return render(request, "profile/profile_questions.html", context)
    
### Profile Diseases Page
@login_required(login_url='login')
def profile_diseases(request):
    user = request.user
    profile = Profile.objects.filter(user= request.user).first()
    diseases = Disease.objects.filter(user=user).all().order_by("-created_on")
    found = 0

    if diseases:
        found = found + 1
        context = {
            'found': found,
            'profile': profile,
            "diseases": diseases,
        }
    else:
        context = {
            'found': found,
            'profile': profile,
        }
    return render(request, "profile/profile_diseases.html", context)

####################################################################################################
####################################################################################################
