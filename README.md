# Call Your Mom!

This is a web application meant to remind you to do some periodic tasks.

After signing up with your email, you can set tasks that should be done every N days, and the system will remind you when it is time. By clicking the link in the email, you can set the next time it should be done.

## Development status

This should be close to ready, but hasn't been tested very much just yet.

Expect this to be deployed publicly in a few days.

Contributions welcome!

## Motivation

I am a software engineer. I use things like bug trackers and boards to organize my tasks, and tend to treat my inbox as a prioritized job queue as well.

However none of those systems are meant for tasks that need to happen again and again.

Not everything is scriptable, but I will do all I can to make those manual tasks a breeze.

## Can't you just mark your calendar?

I don't know in advance when it will be a good time to do one of those tasks again. I don't want to go through the trouble of postponing it in the calendar over and over. There is also the risk that I will not see it, and then I will never be reminded again.

That unread message sitting in my inbox will burn my eyes until I take care of it.

## What can I use this for?

There are two types of tasks:

* The ones that should not be forgotten too long (like calling your mom. If you call her before being reminded, or she calls you, good for you. The reminder will start counting down from that date, so the reminder date changes). Examples:
  * Backup your computer and phone
  * Clean the floors
  * Write a blog post
  * Date night
  * Schedule a meeting for your project
  * Call your mom!
* The ones that need to happen on a specific day exactly (like things you only do on weekends, or on Wednesdays, or the first day of the month). No matter when you acknowledge the reminder, the system will keep to the initial schedule. Examples:
  * Team meeting
  * Play the Nuclear Throne weekly

## How do I install or deploy this

This is a WSGI app using Django. To install it, you will need Python 3 and [pipenv](https://docs.pipenv.org/), then do `pipenv install`.

Copy `website/settings.py.sample` to `website/settings.py` and read it over.

Run `pipenv run python manage.py migrate` to setup the database (`db.sqlite3` by default).

To start the development server, you can use `pipenv run python manage.py runserver`.

To deploy this, you can use the WSGI app `website.wsgi`.

## How do I use this with Docker

The Dockerfile can be used to set this up for development easily. You can start the server with:

```sh
# Builds the image
docker build -t call_your_mom .
# Runs the server
docker run -ti --rm -p 8000:8000 -v $PWD/website:/usr/src/app/website -v $PWD/call_your_mom:/usr/src/app/call_your_mom call_your_mom
```
