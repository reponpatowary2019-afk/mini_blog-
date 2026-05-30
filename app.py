import json
import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, abort

app = Flask(__name__)
app.secret_key = 'mini-blog-dev-secret'

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'posts.json')


# ── Storage helpers (Model layer) ─────────────────────────────────────────────

def load_posts():
    """Read posts from the JSON file. Returns an empty list on any error."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError, OSError):
        return []


def save_posts(posts):
    """Write the posts list back to the JSON file."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)


def read_time(content):
    """Return estimated reading time in minutes (min 1)."""
    return max(1, len(content.split()) // 200)


# ── Routes (View / Controller layer) ─────────────────────────────────────────

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    GET  /  — display all posts and the add-post form.
    POST /  — validate the form; on success save and redirect (PRG pattern);
              on failure re-render the form with errors and preserved input.
    """
    errors = {}
    form_data = {}

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        form_data = {'title': title, 'content': content}

        # Server-side validation
        if not title:
            errors['title'] = 'Title is required.'
        elif len(title) > 200:
            errors['title'] = 'Title must be 200 characters or fewer.'

        if not content:
            errors['content'] = 'Content is required.'

        if not errors:
            posts = load_posts()
            new_post = {
                'id': str(uuid.uuid4()),
                'title': title,
                'content': content,
                'created_at': datetime.now().strftime('%B %d, %Y'),
            }
            # Insert at the front so newest posts appear first
            posts.insert(0, new_post)
            save_posts(posts)
            flash('Post published successfully!', 'success')
            return redirect(url_for('index'))   # Post/Redirect/Get pattern

    posts = load_posts()
    return render_template('index.html', posts=posts, errors=errors, form_data=form_data)


@app.route('/post/<post_id>')
def post_detail(post_id):
    """GET /post/<id> — full-page single post view."""
    posts = load_posts()
    post = next((p for p in posts if p['id'] == post_id), None)
    if post is None:
        abort(404)
    post['read_time'] = read_time(post['content'])
    others = [p for p in posts if p['id'] != post_id][:3]
    for p in others:
        p['read_time'] = read_time(p['content'])
    return render_template('post.html', post=post, others=others)


if __name__ == '__main__':
    app.run(debug=True)
