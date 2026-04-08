import { callBackend } from './api.js?v=5';
import { 
    showToast, setDynamicGlow, ThemeColors, 
    generateDashboardHTML, generateSubjectHTML, 
    generateRequestFormHTML, generateRequestsPanelHTML,
    generateEditModalHTML 
} from './ui.js?v=5';

class Application {
    constructor() {
        this.state = { user: null, role: null, subjects: [] };
        this.currentRoute = null;
        this.currentParams = null;
        window.App = this; 
        this.ui = { showToast, setDynamicGlow };

        // AUTO-SYNC: Fetches fresh data silently when user returns to the browser tab
        window.addEventListener('focus', () => {
            if (this.state.user) {
                this.syncData(true);
            }
        });
    }

    async syncData(silent = false) {
        if (!this.state.user) return;
        const icon = document.getElementById('sync-icon');
        if (icon && !silent) icon.classList.add('animate-spin');

        try {
            const subRes = await callBackend('fetch_dashboard', [this.state.role, this.state.user.id]);
            if (subRes.status === 'success') {
                this.state.subjects = subRes.payload || [];
                this.updateSidebarLinks();
            }

            const outlet = document.getElementById('main-outlet');

            if (this.currentRoute === 'dashboard') {
                outlet.innerHTML = `
                <div class="max-w-6xl mx-auto fade-in">
                    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-6">
                        ${generateDashboardHTML(this.state.subjects)}
                    </div>
                </div>`;
            } 
            else if (this.currentRoute === 'requests' && this.state.role === 'teacher') {
                const reqRes = await callBackend('view_requests', [this.state.user.id]);
                if (reqRes.status === 'success') {
                    outlet.innerHTML = generateRequestsPanelHTML(reqRes.payload, 'teacher');
                }
            }
            else if (this.currentRoute === 'subject' && this.currentParams) {
                const theme = ThemeColors[this.currentParams.themeIndex % ThemeColors.length];
                const detailRes = await callBackend('fetch_subject_details', [this.currentParams.code]);
                if (detailRes.status === 'success') {
                    outlet.innerHTML = generateSubjectHTML(detailRes.payload, theme);
                }
            }

            if (!silent) showToast("Live Sync Complete. Data refreshed.", "success");
            
        } catch (e) {
            if (!silent) showToast("Failed to sync data.", "error");
        } finally {
            if (icon && !silent) setTimeout(() => icon.classList.remove('animate-spin'), 500);
        }
    }

    updateSidebarLinks() {
        document.getElementById('sidebar-dynamic-links').innerHTML = this.state.subjects.map((sub, idx) => `
            <button onclick="window.App.router.navigate('subject', {code: '${sub.subject_code}', themeIndex: ${idx}}); window.App.toggleMenu();" class="flex items-center gap-3 px-3 py-3 rounded-lg hover:bg-gcDark transition text-left text-sm text-textPrimary">
                <span class="truncate">📚 ${sub.subject_code}</span>
            </button>
        `).join('');
    }

    toggleLoginFields() {
        const role = document.querySelector('input[name="login_role"]:checked').value;
        const passInput = document.getElementById('login-pass');
        const idInput = document.getElementById('login-id');
        const hint = document.getElementById('login-hint');

        if (role === 'student') {
            passInput.placeholder = "Full Name";
            idInput.placeholder = "Student ID (e.g., RA24...)";
            hint.innerText = "*Students: Use your Full Name as your password.";
        } else {
            passInput.placeholder = "Secure PIN";
            idInput.placeholder = "Faculty ID (e.g., F1...)";
            hint.innerText = "*Faculty: Use your secure 4-digit PIN.";
        }
    }

    toggleSignupFields() {
        const role = document.querySelector('input[name="signup_role"]:checked').value;
        const pinInput = document.getElementById('reg-pin');
        const idInput = document.getElementById('reg-id');

        if (role === 'student') {
            pinInput.classList.add('hidden');
            pinInput.classList.remove('block');
            pinInput.value = ''; 
            pinInput.removeAttribute('required'); 
            idInput.placeholder = "Student ID (e.g., RA24...)";
        } else {
            pinInput.classList.remove('hidden');
            pinInput.classList.add('block');
            pinInput.setAttribute('required', 'true');
            idInput.placeholder = "Faculty ID (e.g., F1...)";
        }
    }

    toggleAuthMode(mode) {
        if (mode === 'login') {
            document.getElementById('form-login').classList.replace('hidden', 'flex');
            document.getElementById('form-signup').classList.replace('flex', 'hidden');
            document.getElementById('tab-login').className = "px-4 py-2 text-gcBlue border-b-2 border-gcBlue font-medium transition";
            document.getElementById('tab-signup').className = "px-4 py-2 text-textSecondary hover:text-white border-b-2 border-transparent transition";
            document.getElementById('auth-title').innerText = "Academic Portal";
            this.toggleLoginFields();
        } else {
            document.getElementById('form-login').classList.replace('flex', 'hidden');
            document.getElementById('form-signup').classList.replace('hidden', 'flex');
            document.getElementById('tab-signup').className = "px-4 py-2 text-gcBlue border-b-2 border-gcBlue font-medium transition";
            document.getElementById('tab-login').className = "px-4 py-2 text-textSecondary hover:text-white border-b-2 border-transparent transition";
            document.getElementById('auth-title').innerText = "Create Account";
            this.toggleSignupFields();
        }
    }

    async signup(event) {
        event.preventDefault();
        const role = document.querySelector('input[name="signup_role"]:checked').value;
        const uid = document.getElementById('reg-id').value.trim().toUpperCase();
        const name = document.getElementById('reg-name').value;
        const dept = document.getElementById('reg-dept').value;
        const pin = document.getElementById('reg-pin').value;

        if (role === 'teacher' && !pin) {
            showToast("Faculty registration requires a PIN.", "error"); return;
        }

        const res = await callBackend('register_user', [uid, name, dept, role, pin]);
        if (res.status === 'success') {
            showToast("Account created successfully. Please log in.", "success");
            this.toggleAuthMode('login');
        } else {
            // FIX: Now displays dynamic backend errors instead of the hardcoded admin message
            showToast(res.message || "Registration failed.", "error");
        }
    }

    async login(event) {
        event.preventDefault();
        const uid = document.getElementById('login-id').value.trim().toUpperCase();
        const pass = document.getElementById('login-pass').value;
        const radioRole = document.querySelector('input[name="login_role"]:checked').value;

        const backendRole = uid.startsWith('F') ? 'teacher' : (uid.startsWith('S') || uid.startsWith('R') ? 'student' : 'unknown');
        if (radioRole !== backendRole && backendRole !== 'unknown') {
            showToast(`ID format mismatch. '${uid}' belongs to a different role.`, 'error'); return;
        }

        const res = await callBackend('authenticate_user', [uid, pass]);
        
        if (res.status === 'success' && res.payload) {
            let actualName = res.payload.name || uid;
            if (radioRole === 'teacher') actualName = `Prof. ${actualName}`; 

            this.state.user = { id: uid, name: actualName }; 
            this.state.role = radioRole;
            
            const subRes = await callBackend('fetch_dashboard', [this.state.role, uid]);
            if (subRes.status === 'success') this.state.subjects = subRes.payload || [];

            this.initShell();
            this.router.navigate('dashboard');
        } else {
            showToast(res.message || 'Access Denied. Check credentials.', 'error');
        }
    }

    logout() {
        this.state = { user: null, role: null, subjects: [] };
        this.currentRoute = null;
        this.currentParams = null;
        document.getElementById('login-id').value = '';
        document.getElementById('login-pass').value = '';
        document.getElementById('side-menu').classList.remove('translate-x-0');
        document.getElementById('side-menu').classList.add('translate-x-full');
        document.getElementById('view-app').classList.add('hidden');
        document.getElementById('view-auth').classList.remove('hidden');
        setDynamicGlow('#202124');
    }

    initShell() {
        const displayName = this.state.user.name;
        document.getElementById('nav-avatar').innerText = this.state.user.id.charAt(0).toUpperCase();
        document.getElementById('nav-username').innerText = displayName;
        document.getElementById('nav-role').innerText = this.state.role.charAt(0).toUpperCase() + this.state.role.slice(1);
        document.getElementById('menu-greeting').innerText = `Hi, ${displayName}`;

        if (this.state.role === 'student') {
            document.getElementById('menu-btn-edit').classList.add('hidden');
        } else {
            document.getElementById('menu-btn-edit').classList.remove('hidden');
        }

        this.updateSidebarLinks();

        document.getElementById('view-auth').classList.add('hidden');
        document.getElementById('view-app').classList.remove('hidden');
    }

    toggleMenu() {
        document.getElementById('side-menu').classList.toggle('translate-x-full');
        document.getElementById('side-menu').classList.toggle('translate-x-0');
    }

    openEditModal() {
        const modal = document.getElementById('modal-overlay');
        const content = document.getElementById('modal-content');
        content.innerHTML = generateEditModalHTML(this.state.subjects);
        modal.classList.remove('hidden');
        setTimeout(() => content.classList.remove('scale-95'), 10);
    }

    closeModal() {
        const modal = document.getElementById('modal-overlay');
        const content = document.getElementById('modal-content');
        content.classList.add('scale-95');
        setTimeout(() => {
            modal.classList.add('hidden');
            content.innerHTML = '';
        }, 200);
    }

    async submitRequest(event, subjectCode, typeStr = null) {
        event.preventDefault();
        const type = typeStr || document.getElementById('req-type').value;
        const title = document.getElementById('req-title').value;
        const url = document.getElementById('req-url').value || "None";
        const code = subjectCode || document.getElementById('req-subject').value;

        const res = await callBackend('submit_request', [this.state.user.id, code, type, title, url]);
        
        if (res.status === 'success') {
            showToast("Request recorded in backend successfully.", "success");
            if (typeStr) this.closeModal(); 
            else this.router.navigate('subject', { code: code, themeIndex: 0 });
        } else {
            showToast(res.message || "Failed to submit request.", "error");
        }
    }

    router = {
        navigate: async (route, params = null) => {
            const outlet = document.getElementById('main-outlet');
            this.currentRoute = route; 
            this.currentParams = params;
            document.getElementById('side-menu').classList.add('translate-x-full');
            document.getElementById('side-menu').classList.remove('translate-x-0');
            
            if (route === 'dashboard') {
                setDynamicGlow('#202124');
                outlet.innerHTML = `
                <div class="max-w-6xl mx-auto fade-in">
                    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-6">
                        ${generateDashboardHTML(this.state.subjects)}
                    </div>
                </div>`;
                this.syncData(true);
            } 
            else if (route === 'subject') {
                outlet.innerHTML = `<div class="flex justify-center mt-20"><span class="text-textSecondary animate-pulse">Loading Subject...</span></div>`;
                const theme = ThemeColors[params.themeIndex % ThemeColors.length];
                setDynamicGlow(theme.hex);
                
                const res = await callBackend('fetch_subject_details', [params.code]);
                if (res.status === 'success') {
                    outlet.innerHTML = generateSubjectHTML(res.payload, theme);
                } else {
                    outlet.innerHTML = `<p class="text-red-400">Database Error: Failed to load components.</p>`;
                }
            }
            else if (route === 'submit_request') {
                const theme = ThemeColors[params.themeIndex % ThemeColors.length];
                setDynamicGlow(theme.hex);
                outlet.innerHTML = generateRequestFormHTML(params.code, theme);
            }
            else if (route === 'requests') {
                outlet.innerHTML = `<div class="flex justify-center mt-20"><span class="text-textSecondary animate-pulse">Loading Requests...</span></div>`;
                setDynamicGlow('#202124');
                if (this.state.role === 'teacher') {
                    const res = await callBackend('view_requests', [this.state.user.id]);
                    if (res.status === 'success') outlet.innerHTML = generateRequestsPanelHTML(res.payload, 'teacher');
                    else outlet.innerHTML = `<p class="text-red-400">Database Error: Could not fetch pending requests.</p>`;
                } else {
                    outlet.innerHTML = generateRequestsPanelHTML([], 'student');
                }
            }
        }
    }
}

new Application();


