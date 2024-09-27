from datetime import datetime
import humanize
from config import property_uploads_dir, SECRET_KEY
import pytz
from flask import render_template, redirect, url_for, jsonify, request
import jwt
from functools import wraps


def format_date(date_str):
    # Parse the input date string (in format y-m-d)
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    
    # Format the date to "28 Aug, 2024" style
    formatted_date = date_obj.strftime('%d %b, %Y')
    
    return formatted_date


def format_time(time_str):
    # Parse the input time string (in format HH:MM:SS)
    time_obj = datetime.strptime(time_str, '%H:%M:%S')
    
    # Format the time to "12:00 PM" style
    formatted_time = time_obj.strftime('%I:%M %p')
    
    return formatted_time


def process_response(data):
    """ Helper function to process response data. """
    data['property_imgs'] = property_uploads_dir
    for prop in data['items']:
        # Process price
        price = float(prop['price'])
        prop['price'] = humanize.intcomma(int(price) if price.is_integer() else price)
        
        # Process bathrooms
        bathrooms = float(prop['bathrooms'])
        prop['bathrooms'] = int(bathrooms) if bathrooms.is_integer() else bathrooms
        
        # Convert created_at to humanized time
        prop['created_at'] = humanize_time(prop['created_at'])

    return data


def humanize_time(timestamp_str):
    """ Convert ISO timestamp to human-readable format. """
    parsed_date = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    parsed_date = pytz.UTC.localize(parsed_date).astimezone(pytz.timezone("Africa/Lagos"))
    return humanize.naturaltime(parsed_date)


def render_search(data, logged_in, total, current_page, size, total_pages, prf, profile_picture):
    """ Helper function to render the search page. """
    return render_template(
        'search.html',
        data=data,
        logged_in=logged_in,
        total=total,
        page=current_page,
        size=size,
        total_pages=total_pages,
        prf=prf,
        profile_picture=profile_picture
    )


def humanize_res(data):
    for prop in data['items']:
        price = prop['price']
        bathrooms = prop['bathrooms']
        if price.is_integer():
            price = int(price)
        
        if bathrooms.is_integer():
            bathrooms = int(bathrooms)

        humanized_price = humanize.intcomma(price)
        prop['bathrooms'] = bathrooms
        prop['price'] = humanized_price
        timestamp_str = prop['created_at']

        # Parse the string with strptime to handle the Z at the end
        parsed_date = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')

        # Localize to a specific timezone (Africa/Lagos)
        # First, convert parsed_date to UTC and then to Africa/Lagos timezone
        utc_zone = pytz.timezone("UTC")
        lagos_zone = pytz.timezone("Africa/Lagos")

        parsed_date = utc_zone.localize(parsed_date)  # localize to UTC
        timestamp = parsed_date.astimezone(lagos_zone)  # convert to Lagos time

        # Alternatively, you can use humanize to make it more natural, like "2 days ago"
        humanized_time = humanize.naturaltime(timestamp)
        prop['created_at'] = humanized_time

    return data


def humanize_res_single(data):

    price = data['price']
    bathrooms = data['bathrooms']
    if price.is_integer():
        price = int(price)
    
    if bathrooms.is_integer():
        bathrooms = int(bathrooms)

    humanized_price = humanize.intcomma(price)
    data['bathrooms'] = bathrooms
    data['price'] = humanized_price
    # Assume data contains a 'timestamp' field in string format
    timestamp_str = data['created_at']

    # Parse the string with strptime to handle the Z at the end
    parsed_date = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')

    # Localize to a specific timezone (Africa/Lagos)
    # First, convert parsed_date to UTC and then to Africa/Lagos timezone
    utc_zone = pytz.timezone("UTC")
    lagos_zone = pytz.timezone("Africa/Lagos")

    parsed_date = utc_zone.localize(parsed_date)  # localize to UTC
    timestamp = parsed_date.astimezone(lagos_zone)  # convert to Lagos time

    # Alternatively, you can use humanize to make it more natural, like "2 days ago"
    humanized_time = humanize.naturaltime(timestamp)
    data['created_at'] = humanized_time

    return data


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('access_token')
        if not token:
            return redirect(url_for('login'))
        
        try:
            # Decode the token to verify its validity
            jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return redirect(url_for('login'))  # Token expired, redirect to login
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401
        
        return f(*args, **kwargs)
    
    return decorated


def verify_token(token):
    try:
        # Decode the JWT token (use your secret key here)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

