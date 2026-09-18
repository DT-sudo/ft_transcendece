"""The Privacy Policy and Terms of Service in English: the source the translations follow.

`updated` is the date the wording last changed, as shown on the page.
"""

from __future__ import annotations

CONTACT_EMAIL = "privacy@planshift.example"
LAST_UPDATED = "18 September 2026"

PRIVACY_POLICY = {
    "title": "Privacy Policy",
    "updated": LAST_UPDATED,
    "intro": [
        "PlanShift is a shift-scheduling application for hourly-employment teams. "
        "This policy explains exactly what personal data the application holds, why it holds it, "
        "who is able to see it, and what you can ask us to do with it.",
        "PlanShift was built as a student project for the 42 curriculum. It is self-hosted: the "
        "organisation that runs the instance you are using is the data controller, and the "
        "PlanShift authors have no access to it.",
    ],
    "sections": [
        {
            "heading": "1. Data we collect",
            "paragraphs": [
                "We only collect what the scheduling features actually need. There is no analytics "
                "script, no advertising network, no tracking pixel and no third-party embed other "
                "than the web font served by Google Fonts.",
            ],
            "bullets": [
                "Account data — your full name, email address (which is also your login), a "
                "system-generated employee ID, your role (admin, manager or employee), for employees "
                "the position you work, and when the account was created and last signed in.",
                "Profile data — an optional profile picture (re-encoded to a small WebP, which "
                "strips any camera or location metadata), an optional short bio, your friends and "
                "friend requests, and your online status: whether you have PlanShift open, and when "
                "you last did.",
                "Password — never stored as text. Only a salted PBKDF2-SHA256 hash is written to "
                "the database, and it cannot be reversed back into your password.",
                "Two-factor authentication, if you turn it on — the secret your authenticator app "
                "shares with PlanShift (the server needs it to check your codes), when you turned it "
                "on, and your recovery codes, of which only a keyed hash is kept. Turning two-factor "
                "authentication off deletes all of it.",
                "Scheduling data — the shifts you are assigned to, their dates, times, position "
                "and capacity, and the days you have marked yourself unavailable. For managers, "
                "also the shifts they created.",
                "Notifications — the in-app messages about changes other people made that concern "
                "you, such as a shift you were assigned to, and the error messages the application "
                "showed you. They are kept until you clear them or your account is deleted.",
                "Language — the language you use PlanShift in, saved on your account and in a cookie, so "
                "the application, emails and notifications reach you in a language you read.",
                "Security log — a line for each sign-in (successful or failed), sign-out, account or "
                "role change and ended session, with the account's number and login email and the IP "
                "address the request came from. It is written to the server's log, not to the "
                "database, and never contains passwords or codes.",
                "Cookies — a session cookie that keeps you signed in, a CSRF cookie that protects "
                "forms, a language cookie, and a messages cookie that carries a one-off confirmation "
                "or error message to the next page. Section 7 describes them.",
            ],
        },
        {
            "heading": "2. Why we process it",
            "bullets": [
                "To authenticate you and keep your session open between requests.",
                "To build, validate and display the work schedule — including checking that an "
                "assignment matches the employee's position and does not clash with another shift "
                "or a day they marked unavailable.",
                "To let the managers see the roster they run and the hours it allocates to each "
                "person, and to let the admin keep the accounts and positions up to date.",
                "To tell you about changes that concern you, in the application and, for data exports, "
                "account deletion and two-factor authentication changes, by email.",
                "To keep the application secure: rejecting cross-site requests, locking repeated "
                "wrong two-factor codes, and keeping the security log to investigate misuse.",
            ],
            "paragraphs": [
                "The legal basis is the performance of your employment relationship with the "
                "organisation running the instance, together with that organisation's legitimate "
                "interest in operating a work schedule and keeping it secure. We do not process your "
                "data for any purpose beyond running the schedule.",
            ],
        },
        {
            "heading": "3. Who can see your data",
            "bullets": [
                "You — everything about your own account, and a full copy of it on the \"Privacy & "
                "my data\" page.",
                "Colleagues — every signed-in manager and employee sees your name, picture, role or "
                "position and bio on your profile. Your friends also see your email, your friend list "
                "and whether you are online.",
                "Managers — the whole schedule, including draft shifts that employees cannot yet "
                "see, whichever manager created each shift; every employee's name, position and "
                "unavailable days; and the hours each person is scheduled for.",
                "Admins — every account's name, email, employee ID, role, position and whether "
                "two-factor authentication is on. They can change these details, reset a password "
                "or two-factor authentication, and delete accounts.",
                "The operator's technical staff — the people with access to the server, its "
                "database and its logs.",
            ],
            "paragraphs": [
                "Your data is never sold, rented, shared with advertisers, or used to train "
                "machine-learning models. Two outside services see a small part of it: Google Fonts "
                "receives your IP address when your browser downloads the font, and the mail server "
                "the operator configures delivers the emails described above.",
            ],
        },
        {
            "heading": "4. How long we keep it",
            "paragraphs": [
                "Account and scheduling data are kept for as long as your account exists on the "
                "instance. When your account is deleted — by you or by an admin — the account "
                "record, profile picture, friendships, notifications, two-factor data, shift "
                "assignments and unavailability entries are removed from the database at once. "
                "There is no soft-delete and no archive copy. Shifts a manager created stay on the "
                "shared schedule, no longer linked to them.",
                "A one-time generated password is held in the admin's server-side session only "
                "long enough to be shown once, and is discarded as soon as that page is rendered. "
                "Security log lines are kept for as long as the operator keeps the server's logs.",
            ],
        },
        {
            "heading": "5. How we protect it",
            "bullets": [
                "All traffic between your browser and the application is encrypted with TLS; plain "
                "HTTP requests are redirected to HTTPS.",
                "Passwords are stored only as salted PBKDF2-SHA256 hashes.",
                "You can protect your account with two-factor authentication: after your password, "
                "signing in also takes a code from an authenticator app or a one-time recovery code. "
                "Five wrong codes lock the check for five minutes, and every change to it is announced "
                "to you by email.",
                "Every write is protected by a CSRF token, and every page is served with "
                "X-Frame-Options: DENY and X-Content-Type-Options: nosniff.",
                "Access is role-gated on the server: employees cannot reach the schedule or the "
                "account pages, and only ever receive their own published shifts; only admins can "
                "change accounts. When your role changes or your password is reset, your open "
                "sessions are signed out.",
                "Database queries go through the Django ORM, which parameterises every value, and "
                "all rendered content is escaped by default.",
            ],
        },
        {
            "heading": "6. Your rights",
            "paragraphs": [
                "Under the GDPR you may ask for a copy of the data we hold about you, ask for it to "
                "be corrected, ask for it to be deleted, object to its processing, or ask for the "
                "processing to be restricted. You also have the right to complain to your national "
                "data-protection authority.",
                "You can do most of this yourself. On the \"Privacy & my data\" page you can download "
                "everything held about you as a readable JSON file and delete your account after "
                "confirming your email and password; each is confirmed to you by email. Your name, "
                "email, picture and bio can be corrected in Account settings. For anything else, "
                f"write to {CONTACT_EMAIL} or ask the admin of your organisation's instance.",
            ],
        },
        {
            "heading": "7. Cookies",
            "paragraphs": [
                "PlanShift sets four cookies, all strictly necessary for the service to work: the "
                "session cookie that keeps you signed in (for up to two weeks, or until you sign "
                "out), the CSRF cookie that protects forms from cross-site submission, the language "
                "cookie that remembers the language you picked, and the messages cookie that carries "
                "a confirmation or error to the next page and is deleted as soon as it is shown. "
                "None is used for tracking or profiling, so no consent banner is required. Blocking "
                "them will prevent you from logging in.",
            ],
        },
        {
            "heading": "8. Changes to this policy",
            "paragraphs": [
                "If this policy changes, the date at the top of the page is updated. Material "
                "changes will be announced in the application before they take effect.",
            ],
        },
        {
            "heading": "9. Contact",
            "paragraphs": [
                f"Questions about this policy: {CONTACT_EMAIL}. For anything specific to your "
                "schedule, contact your manager; for your account, the admin of your organisation's "
                "instance.",
            ],
        },
    ],
}

TERMS_OF_SERVICE = {
    "title": "Terms of Service",
    "updated": LAST_UPDATED,
    "intro": [
        "These terms govern your use of PlanShift, a shift-scheduling web application. "
        "By creating an account or signing in, you agree to them. If you do not agree, do not use "
        "the service.",
    ],
    "sections": [
        {
            "heading": "1. The service",
            "paragraphs": [
                "PlanShift lets managers build one shared work schedule on a calendar and publish it "
                "to the team, lets employees see the shifts assigned to them and declare the days "
                "they are unavailable, and lets an admin keep the accounts and positions. Colleagues "
                "can view each other's profiles and add each other as friends. It is a planning "
                "tool. It is not a payroll system, a time clock, or a system of record for hours "
                "actually worked.",
            ],
        },
        {
            "heading": "2. Accounts",
            "bullets": [
                "Signing up opens a manager account. The first admin is appointed by the operator "
                "of the instance; admins then create the other accounts and choose their roles.",
                "Accounts an admin creates get a generated password, shown to the admin exactly once; "
                "the admin is responsible for delivering it securely.",
                "You must give an accurate name and a working email address, and you must be at "
                "least 16 years old, or have your guardian's consent, to hold an account.",
                "You are responsible for everything done under your account. Keep your password "
                "secret, do not share the account, and tell your admin immediately if you think "
                "someone else has access to it.",
            ],
        },
        {
            "heading": "3. Acceptable use",
            "paragraphs": ["You agree not to:"],
            "bullets": [
                "Access, or try to access, any account or data your role does not give you access to.",
                "Probe, scan or test the security of the instance, or bypass any access control, "
                "rate limit or authentication check.",
                "Automate requests in a way that degrades the service for other users.",
                "Upload or enter unlawful, abusive or deliberately misleading content, including "
                "offensive profile pictures or bios, false names, or scheduling data entered to harm "
                "a colleague.",
                "Copy, scrape or redistribute another organisation's data.",
            ],
        },
        {
            "heading": "4. Admins' and managers' responsibilities",
            "paragraphs": [
                "Admins and managers act for the organisation running the instance, which is the data "
                "controller for everything entered into it. They are responsible for entering only "
                "the personal data the schedule needs, for having a lawful basis to process it, for "
                "telling the team that PlanShift is in use, and for honouring their requests to "
                "access, correct or delete their data. Our Privacy Policy explains what the "
                "application stores.",
            ],
        },
        {
            "heading": "5. Schedules are not contracts",
            "paragraphs": [
                "A published shift is an operational plan, not a binding offer of work, a guarantee "
                "of hours, or an employment contract. Your rights as an employee come from your "
                "employment agreement and the law of your country, not from anything shown in this "
                "application. Marking yourself unavailable prevents an assignment in the tool; it "
                "does not by itself constitute approved leave.",
            ],
        },
        {
            "heading": "6. Availability",
            "paragraphs": [
                "The service is provided on an \"as is\" and \"as available\" basis. We do not "
                "guarantee that it will be uninterrupted or error-free, and the instance may be "
                "taken down for maintenance, upgrades or at the operator's discretion. Keep your own "
                "record of anything you cannot afford to lose.",
            ],
        },
        {
            "heading": "7. Intellectual property",
            "paragraphs": [
                "The PlanShift source code is released under the MIT License and may be used, "
                "modified and redistributed under its terms. The scheduling and account data held in "
                "an instance belongs to the organisation running it, not to the authors of the "
                "software.",
            ],
        },
        {
            "heading": "8. Suspension and termination",
            "paragraphs": [
                "An admin may delete any account at any time, for example when someone leaves the "
                "team, and the operator of the instance may suspend any account that breaches these "
                "terms. You may stop using the service at any time and delete your account yourself "
                "on the \"Privacy & my data\" page. Deletion removes your account, profile, "
                "friendships, notifications, assignments and unavailability records; shifts you "
                "created as a manager stay on the shared schedule.",
            ],
        },
        {
            "heading": "9. Limitation of liability",
            "paragraphs": [
                "To the fullest extent permitted by law, the authors and the operator of the "
                "instance are not liable for indirect or consequential loss arising from use of the "
                "service, including missed shifts, lost wages, or scheduling errors. Nothing in "
                "these terms limits liability that cannot lawfully be limited.",
            ],
        },
        {
            "heading": "10. Changes to these terms",
            "paragraphs": [
                "We may update these terms. The date at the top of the page shows when they last "
                "changed, and continuing to use the service after a change means you accept the new "
                "version.",
            ],
        },
        {
            "heading": "11. Governing law and contact",
            "paragraphs": [
                "These terms are governed by the law of the country in which the instance is "
                f"operated. Questions about them can be sent to {CONTACT_EMAIL}.",
            ],
        },
        {
            "heading": "12. Academic project notice",
            "paragraphs": [
                "PlanShift was built as part of the 42 school curriculum. It is a demonstration "
                "project: it has not been through a formal security audit or legal review, and it "
                "should be assessed accordingly before being relied on for real payroll-adjacent "
                "decisions.",
            ],
        },
    ],
}

DOCUMENTS = {"privacy": PRIVACY_POLICY, "terms": TERMS_OF_SERVICE}
