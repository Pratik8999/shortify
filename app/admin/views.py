from sqladmin import ModelView
from app.models import User, Url, UrlAnalytics, AppVisit
from app.auth.hashing import hash_password
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired, Length, Optional as OptionalValidator
from sqlalchemy import Column


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.name, User.email, User.country, User.isactive, User.createdon, User.updatedon]
    column_searchable_list = [User.email, User.country]
    column_sortable_list = [User.id, User.email, User.createdon]
    column_details_exclude_list = [User.password]
    
    # Don't exclude password from form - we'll override it
    form_excluded_columns = [User.urls, User.createdon, User.updatedon]
    
    # Override the password field with a PasswordField widget
    form_overrides = {
        "password": PasswordField
    }
    
    # Customize form args for password field
    form_args = {
        "password": {
            "label": "Password",
            "validators": [OptionalValidator()],
            "description": "Enter plain password (will be hashed automatically). Leave empty to keep existing password when updating."
        }
    }
    
    async def on_model_change(self, data, model, is_created, request):
        """
        Hash password before saving to database.
        Called before creating or updating a user.
        """
        # Check if password field has data
        if "password" in data and data["password"]:
            # Hash the plain password
            hashed = hash_password(data["password"])
            data["password"] = hashed
        elif is_created:
            # If creating new user without password, raise error
            raise ValueError("Password is required when creating a new user")
        
        return await super().on_model_change(data, model, is_created, request)
    
    def on_model_delete(self, model):
        """
        Optional: Add any cleanup logic before deleting a user
        """
        pass


class UrlAdmin(ModelView, model=Url):
    column_list = [Url.id, Url.code, Url.url, Url.user, Url.click_count, Url.expires_at, Url.createdon, Url.updatedon]
    column_searchable_list = [Url.code, Url.url]
    column_sortable_list = [Url.id, Url.code, Url.click_count, Url.createdon]
    column_default_sort = [(Url.createdon, True)]  # Sort by newest first
    
    # Read-only fields
    form_excluded_columns = [Url.user_ref, Url.analytics, Url.createdon, Url.updatedon]
    
    # Display foreign key relationship nicely
    column_formatters = {
        Url.url: lambda model, a: model.url[:50] + "..." if len(model.url) > 50 else model.url
    }
    
    form_args = {
        "code": {
            "label": "Short Code",
            "description": "Unique short code for the URL"
        },
        "url": {
            "label": "Original URL",
            "description": "The original long URL"
        },
        "click_count": {
            "label": "Click Count",
            "description": "Number of times this URL has been accessed"
        }
    }


class UrlAnalyticsAdmin(ModelView, model=UrlAnalytics):
    column_list = [UrlAnalytics.id, UrlAnalytics.url, UrlAnalytics.ip_address, UrlAnalytics.country, 
                   UrlAnalytics.device, UrlAnalytics.browser, UrlAnalytics.os, UrlAnalytics.createdon]
    column_searchable_list = [UrlAnalytics.ip_address, UrlAnalytics.country, UrlAnalytics.browser, UrlAnalytics.device]
    column_sortable_list = [UrlAnalytics.id, UrlAnalytics.country, UrlAnalytics.createdon]
    column_default_sort = [(UrlAnalytics.createdon, True)]  # Sort by newest first
    
    # Read-only fields
    form_excluded_columns = [UrlAnalytics.url_ref, UrlAnalytics.createdon, UrlAnalytics.updatedon]
    
    # Truncate long fields for display
    column_formatters = {
        UrlAnalytics.user_agent: lambda model, a: model.user_agent[:50] + "..." if model.user_agent and len(model.user_agent) > 50 else model.user_agent,
        UrlAnalytics.referrer: lambda model, a: model.referrer[:40] + "..." if model.referrer and len(model.referrer) > 40 else model.referrer
    }
    
    form_args = {
        "url": {
            "label": "URL ID",
            "description": "Foreign key reference to the URL"
        },
        "ip_address": {
            "label": "IP Address",
            "description": "Visitor's IP address"
        }
    }


class AppVisitAdmin(ModelView, model=AppVisit):
    name = "App Visit"
    name_plural = "App Visits"
    icon = "fa-solid fa-chart-line"
    
    column_list = [AppVisit.id, AppVisit.ip_address, AppVisit.country, AppVisit.city, 
                   AppVisit.region, AppVisit.timezone, AppVisit.org, AppVisit.createdon, AppVisit.updatedon]
    column_searchable_list = [AppVisit.ip_address, AppVisit.country, AppVisit.city, 
                             AppVisit.region, AppVisit.org, AppVisit.postal]
    column_sortable_list = [AppVisit.id, AppVisit.country, AppVisit.city, 
                           AppVisit.createdon, AppVisit.updatedon]
    column_default_sort = [(AppVisit.createdon, True)]  # Sort by newest first
    
    # Show all details in the detail view
    column_details_list = [
        AppVisit.id,
        AppVisit.ip_address,
        AppVisit.country,
        AppVisit.city,
        AppVisit.region,
        AppVisit.latitude,
        AppVisit.longitude,
        AppVisit.timezone,
        AppVisit.org,
        AppVisit.postal,
        AppVisit.createdon,
        AppVisit.updatedon
    ]
    
    # Read-only fields - prevent modification of timestamps
    form_excluded_columns = [AppVisit.createdon, AppVisit.updatedon]
    
    # Truncate long fields for display
    column_formatters = {
        AppVisit.org: lambda model, a: model.org[:50] + "..." if model.org and len(model.org) > 50 else model.org,
        AppVisit.ip_address: lambda model, a: f"<code>{model.ip_address}</code>" if model.ip_address else None
    }
    
    # Add labels for better column headers
    column_labels = {
        "id": "ID",
        "ip_address": "IP Address",
        "country": "Country",
        "city": "City",
        "region": "Region/State",
        "latitude": "Latitude",
        "longitude": "Longitude",
        "timezone": "Timezone",
        "org": "ISP/Organization",
        "postal": "Postal Code",
        "createdon": "First Visit",
        "updatedon": "Last Updated"
    }
    
    form_args = {
        "ip_address": {
            "label": "IP Address",
            "description": "Unique visitor IP address (IPv4 or IPv6)",
            "validators": [DataRequired()]
        },
        "country": {
            "label": "Country",
            "description": "Visitor's country (2-letter code or full name)"
        },
        "city": {
            "label": "City",
            "description": "Visitor's city"
        },
        "region": {
            "label": "Region/State",
            "description": "Visitor's region or state"
        },
        "latitude": {
            "label": "Latitude",
            "description": "Geographic latitude coordinate"
        },
        "longitude": {
            "label": "Longitude",
            "description": "Geographic longitude coordinate"
        },
        "timezone": {
            "label": "Timezone",
            "description": "Visitor's timezone (e.g., America/New_York)"
        },
        "org": {
            "label": "ISP/Organization",
            "description": "Internet Service Provider or organization"
        },
        "postal": {
            "label": "Postal Code",
            "description": "Visitor's postal/zip code"
        }
    }
    
    # Enable pagination
    page_size = 50
    page_size_options = [25, 50, 100, 200]
    
    # Make it read-only by default (optional - remove if you want editing)
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    