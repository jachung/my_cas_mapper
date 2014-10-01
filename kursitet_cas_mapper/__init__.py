"""
Beyond the original function of CAS attribute mapper, this should also manage other objects...
""" 

CAS_URI = 'http://www.yale.edu/tp/cas'

NSMAP = {'cas': CAS_URI}
CAS = '{%s}' % CAS_URI

def populate_user(user, authentication_response):
    if authentication_response.find(CAS + 'authenticationSuccess/'  + CAS + 'attributes'  , namespaces=NSMAP) is not None:
        attr = authentication_response.find(CAS + 'authenticationSuccess/'  + CAS + 'attributes'  , namespaces=NSMAP)

        if attr.find(CAS + 'is_staff', NSMAP) is not None:
            user.is_staff = attr.find(CAS + 'is_staff', NSMAP).text.upper() == 'TRUE'

        if attr.find(CAS + 'is_superuser', NSMAP) is not None:
            user.is_superuser = attr.find(CAS + 'is_superuser', NSMAP).text.upper() == 'TRUE'

        if attr.find(CAS + 'is_active', NSMAP) is not None:
            user.is_active = attr.find(CAS + 'is_active', NSMAP).text.upper() == 'TRUE'

        # Limiting by maximum lengths.
        # Max length of firstname/lastname is 30.
        # Max length of a email is 75.
        if attr.find(CAS + 'givenName', NSMAP) is not None:
            user.first_name = attr.find(CAS + 'givenName', NSMAP).text[0:30]

        if attr.find(CAS + 'sn', NSMAP) is not None:
            user.last_name = attr.find(CAS + 'sn', NSMAP).text[0:30]

        if attr.find(CAS + 'email', NSMAP) is not None:
            user.email = attr.find(CAS + 'email', NSMAP).text[0:75]
        
        # Here we handle things that go into UserProfile instead.
        
        # This is a dirty hack and you shouldn't do that. 
        # However, I don't think it's going to work when imported outside of the function body.
        
        from student.models import UserProfile
        
        try:
            user_profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            user.save()
            user_profile = UserProfile(user=user)
            
        # Since this branch is for old edX, we need to assemble the full name from three components as well as
        # save them, because it wants the full name in inobvious order (last-first-patronymic).

        if attr.find(CAS + 'givenName', NSMAP) is not None:
            user_profile.firstname = attr.find(CAS + 'givenName', NSMAP).text[0:30]

        if attr.find(CAS + 'sn', NSMAP) is not None:
            user_profile.lastname = attr.find(CAS + 'sn', NSMAP).text[0:30]

        if attr.find(CAS + 'patronymic', NSMAP) is not None:
            user_profile.middlename = attr.find(CAS + 'patronymic', NSMAP).text[0:30]

        # Now that we presumably have all three components, we can assemble them.
        user_profile.name = u' '.join([user_profile.lastname,user_profile.firstname,user_profile.middlename])

        # Profile is always getting saved, just like the user,
        # but the user is getting saved by django_cas.
        user_profile.save()
        
    pass
