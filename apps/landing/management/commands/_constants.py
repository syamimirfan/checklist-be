from apps.landing.models import Tone

FEATURES = [
    {
        'title': 'Shared workspaces',
        'description': 'Invite your team into a workspace and organize checklists together in real time.',
        'tone': Tone.VIOLET,
    },
    {
        'title': 'Templates that stick',
        'description': 'Turn any checklist into a reusable template so recurring work never starts from scratch.',
        'tone': Tone.FUCHSIA,
    },
    {
        'title': 'Tags & due dates',
        'description': 'Keep everything organized with color tags, due dates, and assignees.',
        'tone': Tone.PINK,
    },
    {
        'title': 'Comments built in',
        'description': 'Discuss individual checklist items without leaving the task at hand.',
        'tone': Tone.PURPLE,
    },
]

TESTIMONIALS = [
    {
        'quote': 'Checklist turned our chaotic launch week into something genuinely calm.',
        'author': 'Priya Nair',
        'role': 'Product Lead, Orbital',
    },
    {
        'quote': 'The shared workspaces make handing off tasks between teams painless.',
        'author': 'Marcus Webb',
        'role': 'Operations Manager, Fenwick & Co',
    },
    {
        'quote': 'Simple enough for personal to-dos, powerful enough for our whole company.',
        'author': 'Elena Ruiz',
        'role': 'Founder, Studio Norte',
    },
]
