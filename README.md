# SkillsSync AI - Freelance Job Platform

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://www.djangoproject.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.0+-38B2AC.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

SkillsSync AI is a modern, feature-rich freelance job platform that connects skilled workers with clients seeking professional services. Built with Django and Tailwind CSS, it provides a seamless experience for job posting, application management, and professional networking.

## 🌟 Features

### For Clients
- **Job Management**: Create, edit, and manage job postings
- **Draft System**: Save jobs as drafts and publish when ready
- **Application Review**: Review and manage worker applications
- **Worker Discovery**: Browse and filter skilled professionals
- **Real-time Updates**: Track job status and application progress

### For Workers
- **Profile Management**: Create detailed professional profiles
- **Skill Showcase**: Display skills, experience, and certifications
- **Job Applications**: Apply to relevant job opportunities
- **Portfolio Display**: Showcase completed work and reviews
- **Availability Management**: Set working hours and availability

### Platform Features
- **Advanced Search**: Filter jobs and workers by various criteria
- **Real-time Notifications**: Stay updated on important activities
- **Responsive Design**: Works seamlessly on all devices
- **Dark Mode Support**: Modern UI with dark/light theme toggle
- **Secure Authentication**: User registration, login, and profile management

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/asaiah4812/Skillsync-ai.git
   cd skillsync-ai
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Open your browser**
   Navigate to `http://127.0.0.1:8000/`

## 🏗️ Project Structure

```
skillsync-ai/
├── accounts/                 # User authentication and profiles
├── core/                     # Main application logic
│   ├── models.py            # Database models
│   ├── views.py             # View functions
│   ├── forms.py             # Form definitions
│   └── urls.py              # URL routing
├── templates/                # HTML templates
│   ├── core/                # Core app templates
│   ├── accounts/            # Authentication templates
│   └── layouts/             # Base layout templates
├── static/                   # Static files (CSS, JS, images)
├── media/                    # User-uploaded files
├── project/                  # Django project settings
└── requirements.txt          # Python dependencies
```

## 🎯 Key Models

### User System
- **User**: Extended user model with user type (CLIENT/WORKER)
- **Profile**: Additional user information and preferences

### Job Management
- **Job**: Job postings with detailed requirements
- **Application**: Worker applications for jobs
- **Skill**: Skills and expertise areas
- **Category**: Job categories and classifications

### Worker Features
- **WorkerProfile**: Professional worker information
- **WorkerSkill**: Skills with proficiency levels
- **Availability**: Working hours and availability
- **Rating**: Client reviews and ratings

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Database Configuration
The project supports multiple database backends:
- **SQLite** (default for development)
- **PostgreSQL** (recommended for production)
- **MySQL**

## 🎨 Customization

### Styling
The project uses Tailwind CSS for styling. To customize:
1. Install Tailwind CSS CLI
2. Modify `tailwind.config.js`
3. Rebuild CSS files

### Templates
All templates are located in the `templates/` directory and can be customized to match your brand.

## 📱 API Endpoints

### Authentication
- `POST /accounts/login/` - User login
- `POST /accounts/register/` - User registration
- `POST /accounts/logout/` - User logout

### Jobs
- `GET /jobs/` - Browse all jobs
- `POST /jobs/` - Create new job
- `GET /jobs/{id}/` - Job details
- `PUT /jobs/{id}/` - Update job

### Workers
- `GET /workers/` - Browse all workers
- `GET /workers/{id}/` - Worker profile
- `POST /workers/{id}/apply/` - Apply for job

## 🚀 Deployment

### Production Setup
1. Set `DEBUG=False` in production
2. Configure production database
3. Set up static file serving
4. Configure email backend
5. Set up SSL/HTTPS

### Docker Deployment
```bash
docker build -t skillsync-ai .
docker run -p 8000:8000 skillsync-ai
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 Python style guide
- Write tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting

## 🧪 Testing

Run the test suite:
```bash
python manage.py test
```

Run with coverage:
```bash
coverage run --source='.' manage.py test
coverage report
```

## 📊 Performance

### Optimization Tips
- Use database indexing for frequently queried fields
- Implement caching for static content
- Optimize database queries
- Use CDN for static files in production

## 🔒 Security

### Security Features
- CSRF protection enabled
- SQL injection protection
- XSS protection
- Secure password hashing
- User authentication required for sensitive operations

## 📈 Roadmap

### Upcoming Features
- [ ] Real-time chat system
- [ ] Payment integration
- [ ] Advanced analytics dashboard
- [ ] Mobile app development
- [ ] AI-powered job matching
- [ ] Video call integration

## 🐛 Troubleshooting

### Common Issues

**Database connection errors**
- Check database configuration in settings.py
- Ensure database service is running

**Static files not loading**
- Run `python manage.py collectstatic`
- Check static files configuration

**Migration errors**
- Delete migration files and recreate
- Check model compatibility

## 📞 Support

- **Documentation**: [Wiki](https://github.com/asaiah4812/Skillsync-ai/wiki)
- **Issues**: [GitHub Issues](https://github.com/asaiah4812/skillsync-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/asaiah4812/skillsync-ai/discussions)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Django community for the excellent framework
- Tailwind CSS team for the utility-first CSS framework
- All contributors who have helped improve this project

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/skillsync-ai&type=Date)](https://star-history.com/#yourusername/skillsync-ai&Date)

---

**Made with ❤️ by dreamerwebdev Team**
https://hensonport.vercel.app

If you find this project helpful, please consider giving it a ⭐ star on GitHub!
