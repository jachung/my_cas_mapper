"""
Beyond the original function of CAS attribute mapper, this should also manage other objects...
""" 

import json

CAS_URI = 'http://www.yale.edu/tp/cas'

NSMAP = {'cas': CAS_URI}
CAS = '{%s}' % CAS_URI

def populate_user(user, authentication_response):
    attr = authentication_response.find(CAS + 'authenticationSuccess/'  + CAS + 'attributes'  , namespaces=NSMAP)
    if attr is not None:
    
        staff_flag = attr.find(CAS + 'is_staff', NSMAP)
        if staff_flag is not None:
            user.is_staff = (staff_flag.text or '').upper() == 'TRUE'

        superuser_flag = attr.find(CAS + 'is_superuser', NSMAP)    
        if superuser_flag is not None:
            user.is_superuser = (superuser_flag.text or '').upper() == 'TRUE'

        active_flag = attr.find(CAS + 'is_active', NSMAP)
        if active_flag is not None:
            user.is_active = (active_flag.text or '').upper() == 'TRUE'

        # Limiting by maximum lengths.
        # Max length of firstname/lastname is 30.
        # Max length of a email is 75.
        
        first_name = attr.find(CAS + 'givenName', NSMAP)
        if first_name is not None:
            user.first_name = (first_name.text or '')[0:30]

        last_name = attr.find(CAS + 'sn', NSMAP)
        if last_name is not None:
            user.last_name = (last_name.text or '')[0:30]

        email = attr.find(CAS + 'email', NSMAP)
        if email is not None:
            user.email = (email.text or '')[0:75]
        
        # Here we handle things that go into UserProfile instead.
        
        # This is a dirty hack and you shouldn't do that. 
        # However, I don't think it's going to work when imported outside of the function body.
        
        from student.models import UserProfile
        
        user_profile, created = UserProfile.objects.get_or_create(user=user)
            
        # Since this branch is for old edX, we need to assemble the full name from three components as well as
        # save them, because it wants the full name in inobvious order (last-first-patronymic).

        user_profile.firstname = (first_name.text or '')[0:30]
        user_profile.lastname = (last_name.text or '')[0:30]

        patronymic = attr.find(CAS + 'patronymic', NSMAP)
        if patronymic is not None:
            user_profile.middlename = (patronymic.text or '')[0:30]

        # Now that we presumably have all three components, we can assemble them.
        user_profile.name = u' '.join([user_profile.lastname,user_profile.firstname,user_profile.middlename])

        # Profile is always getting saved, just like the user,
        # but the user is getting saved by django_cas.
        user_profile.save()
        
        # Now the really fun bit. Signing the user up for courses given.
        
        coursetag = attr.find(CAS + 'courses', NSMAP)
        if coursetag is not None and coursetag.text is not None:
            try:
                courses = json.loads(coursetag.text)
                assert isinstance(courses,list)
            except (ValueError, AssertionError):
                # We failed to parse the tag and get a list, so we leave.
                return
            # We got a list, so we need to import the enroll call.
            from student.models import CourseEnrollment
            for course in courses:
                if course:
                    # Notice that we don't check if a course by that ID actually exists!
                    # We don't really have the time for this, 
                    # (I seriously suspect this function is getting called more often than once per login)
                    # and CourseEnrollment objects do no checking of their own.
                    # Being enrolled in a deleted course should not be an issue though...
                    CourseEnrollment.enroll(user,course)
    pass
