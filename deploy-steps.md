# Railway Deployment Steps

## 1. Add PostgreSQL Database
1. Go to your Railway project dashboard.
2. Click **+ New** -> **Database** -> **Add PostgreSQL**.
3. Wait a few seconds for the database to fully provision.

## 2. Connect Your GitHub Repository
1. In the same project dashboard, click **+ New** -> **GitHub Repo**.
2. Select your `icm-django` repository so Railway creates a Web Service for it.

## 3. Link the Database to the Web Service
1. Click on your newly created Web Service (your Django app) in the dashboard.
2. Go to the **Variables** tab.
3. Click **New Variable** -> **Reference Variable**.
4. Select your PostgreSQL service, and pick `DATABASE_URL`.

## 4. Configure Deployment Commands
In your Web Service, go to the **Settings** tab and scroll down to the **Deploy** section. Set the following commands:

- **Build Command**: 
  `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- **Pre-Deploy Command**: 
  `python manage.py migrate --noinput`
- **Start Command**: 
  `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3`

## 5. Set Environment Variables
Go back to the **Variables** tab on your Web Service and add the following:

- `DJANGO_SECRET_KEY`: (Generate a long, secure random string)
- `DJANGO_DEBUG`: `0`
- `DJANGO_ALLOWED_HOSTS`: `<your-railway-domain>` (You can generate your domain in Settings -> Networking)
- `CSRF_TRUSTED_ORIGINS`: `https://<your-railway-domain>`

## 6. Final Verification
1. Railway will likely rebuild your project with the new variables.
2. Verify in the deployment logs that dependencies install, migrations run successfully on the fresh database, and Gunicorn starts.
3. Click on your public URL to test that static files load correctly and DB connections work!
