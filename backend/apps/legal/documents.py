"""Content of the Privacy Policy and Terms of Service.

Kept as data rather than templates so the same structure renders through the
React shell, is easy to review in one place, and can be diffed when the wording
changes. `updated` is the date the wording last changed and is shown on the page.
"""

from __future__ import annotations

CONTACT_EMAIL = "privacy@planshift.example"
LAST_UPDATED = "8 September 2026"

PRIVACY_POLICY = {
    "slug": "privacy",
    "title": "Privacy Policy",
    "summary": "What PlanShift stores about you, why it is stored, who can see it, and how to have it removed.",
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
                "**Account data** — your full name, email address (which is also your login), a "
                "system-generated employee ID, your role (manager or employee) and, for employees, "
                "the position you are qualified for.",
                "**Password** — never stored as text. Only a salted PBKDF2-SHA256 hash is written to "
                "the database, and it cannot be reversed back into your password.",
                "**Scheduling data** — the shifts you are assigned to, their dates, times, position "
                "and capacity, and the days you have marked yourself unavailable.",
                "**Session cookie** — a signed identifier that keeps you logged in. It is "
                "`HttpOnly`, `SameSite=Lax` and `Secure`, so it is unreadable to JavaScript and is "
                "never sent over an unencrypted connection.",
                "**CSRF cookie** — a random token used to prove that a form submission came from a "
                "page we served. It contains no information about you.",
            ],
        },
        {
            "heading": "2. Why we process it",
            "bullets": [
                "To authenticate you and keep your session open between requests.",
                "To build, validate and display work schedules — including checking that an "
                "assignment does not clash with an existing shift or a day you marked unavailable.",
                "To let your manager see the roster they are responsible for and the hours it "
                "allocates to each person.",
                "To keep the application secure, for example by rejecting cross-site requests.",
            ],
            "paragraphs": [
                "The legal basis is the performance of your employment relationship with the "
                "organisation running the instance, together with that organisation's legitimate "
                "interest in operating a work schedule. We do not process your data for any purpose "
                "beyond running the schedule.",
            ],
        },
        {
            "heading": "3. Who can see your data",
            "bullets": [
                "**You** — your own profile, your published shifts and your unavailability.",
                "**Managers in your organisation** — the team directory (name, email, position) and "
                "the full schedule, including draft shifts that employees cannot yet see.",
                "**Administrators of the instance** — technical staff with server or database access.",
            ],
            "paragraphs": [
                "Your data is never sold, rented, shared with advertisers, or transferred to any "
                "third party. It is not used to train machine-learning models.",
            ],
        },
        {
            "heading": "4. How long we keep it",
            "paragraphs": [
                "Account and scheduling data are kept for as long as your account exists on the "
                "instance. When a manager deletes an employee account, the account record, its "
                "shift assignments and its unavailability entries are removed from the database in "
                "the same transaction — there is no soft-delete and no archive copy.",
                "A one-time generated password is held in the manager's server-side session only "
                "long enough to be shown once, and is discarded as soon as that page is rendered.",
            ],
        },
        {
            "heading": "5. How we protect it",
            "bullets": [
                "All traffic between your browser and the application is encrypted with TLS; plain "
                "HTTP requests are redirected to HTTPS.",
                "Passwords are stored only as salted PBKDF2-SHA256 hashes.",
                "Every write is protected by a CSRF token, and every page is served with "
                "`X-Frame-Options: DENY` and `X-Content-Type-Options: nosniff`.",
                "Access is role-gated on the server: an employee cannot reach a manager endpoint, "
                "and requesting another manager's shift by guessing its ID returns 404.",
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
                f"Send any of these requests to {CONTACT_EMAIL} or to the manager of your "
                "organisation, who can update or delete your account directly.",
            ],
        },
        {
            "heading": "7. Cookies",
            "paragraphs": [
                "PlanShift sets two cookies, both strictly necessary for the service to work: the "
                "session cookie that keeps you signed in, and the CSRF cookie that protects forms "
                "from cross-site submission. Neither is used for tracking or profiling, so no "
                "consent banner is required. Blocking them will prevent you from logging in.",
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
                "schedule or your account, contact your manager first — they administer your "
                "organisation's instance.",
            ],
        },
    ],
}

TERMS_OF_SERVICE = {
    "slug": "terms",
    "title": "Terms of Service",
    "summary": "The rules for using PlanShift: accounts, acceptable use, what the schedule does and does not mean, and the limits of our liability.",
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
                "PlanShift lets a manager build a work schedule on a calendar and publish it to "
                "their team, and lets employees see the shifts assigned to them and declare the days "
                "they are unavailable. It is a planning tool. It is not a payroll system, a time "
                "clock, or a system of record for hours actually worked.",
            ],
        },
        {
            "heading": "2. Accounts",
            "bullets": [
                "**Manager accounts** are opened through the sign-up page. Signing up makes you "
                "responsible for the team you then create.",
                "**Employee accounts** are created by a manager, who receives a generated password "
                "shown exactly once and is responsible for delivering it securely.",
                "You must give an accurate name and a working email address, and you must be at "
                "least 16 years old, or have your guardian's consent, to hold an account.",
                "You are responsible for everything done under your account. Keep your password "
                "secret, do not share the account, and tell your manager immediately if you think "
                "someone else has access to it.",
            ],
        },
        {
            "heading": "3. Acceptable use",
            "paragraphs": ["You agree not to:"],
            "bullets": [
                "Access, or try to access, any account, shift or team that is not yours.",
                "Probe, scan or test the security of the instance, or bypass any access control, "
                "rate limit or authentication check.",
                "Automate requests in a way that degrades the service for other users.",
                "Upload or enter unlawful, abusive or deliberately misleading content, including "
                "false names or scheduling data entered to harm a colleague.",
                "Copy, scrape or redistribute another organisation's data.",
            ],
        },
        {
            "heading": "4. Managers' responsibilities",
            "paragraphs": [
                "If you hold a manager account, you decide which personal data about your staff is "
                "entered into the instance, and you are the data controller for it. You are "
                "responsible for having a lawful basis to process it, for telling your team that "
                "PlanShift is in use, and for honouring their requests to access or delete their "
                "data. Our Privacy Policy explains what the application stores on your behalf.",
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
                "A manager may deactivate or delete an employee account at any time, for example "
                "when someone leaves the team. The operator of the instance may suspend any account "
                "that breaches these terms. You may stop using the service at any time and ask your "
                "manager to delete your account; deletion removes your account, assignments and "
                "unavailability records.",
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
