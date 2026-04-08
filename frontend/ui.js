export const ThemeColors = [
    { bg: 'bg-blue-600', text: 'text-blue-400', hex: '#2563eb' },
    { bg: 'bg-gray-600', text: 'text-gray-400', hex: '#4b5563' },
    { bg: 'bg-green-600', text: 'text-green-400', hex: '#16a34a' },
    { bg: 'bg-purple-600', text: 'text-purple-400', hex: '#9333ea' }
];

export function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const color = type === 'error' ? 'bg-red-500 text-white' : 'bg-gcSurface border border-gcBorder text-textPrimary';
    const toast = document.createElement('div');
    toast.className = `${color} px-4 py-3 rounded shadow-lg text-sm font-medium fade-in`;
    toast.innerHTML = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

export function setDynamicGlow(hexColor) {
    document.getElementById('dynamic-bg').style.background = `radial-gradient(circle at 50% 50%, ${hexColor}15 0%, #202124 80%)`;
}

export function generateDashboardHTML(subjects) {
    if (subjects.length === 0) return `<p class="text-textSecondary col-span-full text-center mt-10">No enrolled classes found.</p>`;
    
    return subjects.map((sub, index) => {
        const code = sub.subject_code || 'N/A';
        const name = sub.subject_name || 'Subject Data';
        
        // Dynamic Fields from Backend
        const faculty = sub.faculty_name || 'Unassigned Faculty';
        
        // QUICK FIX: Hardcoded to bypass the database schema issue temporarily
        const section = 'Section: CSE A'; 
        
        const theme = ThemeColors[index % ThemeColors.length];
        const initial = (name || code || 'S').charAt(0).toUpperCase();

        return `
        <div class="subject-card bg-gcSurface border border-gcBorder rounded-lg overflow-hidden relative slide-up group" 
             style="animation-delay: ${index * 0.05}s"
             onmouseenter="window.App.ui.setDynamicGlow('${theme.hex}')"
             onmouseleave="window.App.ui.setDynamicGlow('#202124')">
            
            <div class="${theme.bg} h-24 p-4 relative bg-opacity-90 cursor-pointer" onclick="window.App.router.navigate('subject', { code: '${code}', themeIndex: ${index} })">
                <h2 class="text-white font-medium truncate text-xl group-hover:underline">${code} - ${name}</h2>
                <p class="text-white text-xs opacity-90 mt-1">${section}</p>
                <p class="text-white text-xs opacity-90">${faculty}</p>
            </div>
            
            <div class="absolute top-16 right-4 w-[4.5rem] h-[4.5rem] rounded-full bg-indigo-500 border-4 border-gcSurface flex items-center justify-center text-3xl font-medium text-white shadow-sm z-10 pointer-events-none">
                ${initial}
            </div>

            <div class="p-4 h-28 flex flex-col justify-end">
                <div class="flex justify-end gap-4 text-textSecondary border-t border-gcBorder pt-3">
                    <span class="material-symbols-outlined hover:text-white transition cursor-pointer" title="Instructor Info" onclick="window.App.ui.showToast('Instructor: ${faculty}', 'info'); event.stopPropagation();">person</span>
                    <span class="material-symbols-outlined hover:text-white transition cursor-pointer" title="Open Materials" onclick="window.App.router.navigate('subject', { code: '${code}', themeIndex: ${index} }); event.stopPropagation();">folder_open</span>
                </div>
            </div>
        </div>`;
    }).join('');
}

export function generateSubjectHTML(data, theme) {
    let html = `
    <div class="max-w-5xl mx-auto fade-in pb-20">
        <button onclick="window.App.router.navigate('dashboard')" class="text-textSecondary hover:text-white mb-6 flex items-center gap-2 transition text-sm font-medium">
            <span class="material-symbols-outlined text-sm">arrow_back</span> Back to Dashboard
        </button>

        <div class="h-64 ${theme.bg} rounded-xl p-8 mb-6 flex flex-col justify-end relative overflow-hidden shadow-md">
            <div class="absolute right-0 top-0 opacity-20 text-[200px] pointer-events-none translate-x-1/4 -translate-y-1/4 select-none">🎨</div>
            <h1 class="text-4xl font-medium text-white relative z-10">${data.code} - ${data.name}</h1>
            <p class="text-xl text-white opacity-90 mt-1 relative z-10">${data.faculty || 'Instructor'}</p>
        </div>

        <div class="flex gap-6 items-start flex-col md:flex-row">
            <div class="flex-1 flex flex-col gap-6 w-full">
                <div class="space-y-4">`;

    if (data.components && data.components.length > 0) {
        data.components.forEach((group, gIndex) => {
            html += `
            <div class="bg-gcSurface border border-gcBorder rounded-lg overflow-hidden shadow-sm">
                <div class="p-4 cursor-pointer hover:bg-[#35363a] transition flex justify-between items-center" 
                     onclick="document.getElementById('group-${gIndex}').classList.toggle('open'); document.getElementById('icon-${gIndex}').classList.toggle('rotate-180');">
                    <div class="flex items-center gap-4">
                        <div class="w-10 h-10 rounded-full bg-gcDark flex items-center justify-center text-textSecondary"><span class="material-symbols-outlined text-xl">assignment</span></div>
                        <h3 class="text-base font-medium text-textPrimary">${group.category}</h3>
                    </div>
                    <span class="material-symbols-outlined text-textSecondary transform transition-transform duration-300" id="icon-${gIndex}">expand_more</span>
                </div>
                
                <div id="group-${gIndex}" class="swiss-knife-grid bg-gcDark/30 border-t border-gcBorder">
                    <div class="swiss-knife-inner">
                        <div class="p-4 space-y-2">`;
                        group.links.forEach(link => {
                            html += `
                            <a href="${link.url}" target="_blank" class="flex justify-between items-center p-3 rounded-md hover:bg-gcSurface transition group/link border border-transparent hover:border-gcBorder">
                                <div class="flex items-center gap-3">
                                    <span class="material-symbols-outlined text-gcBlue text-xl">description</span>
                                    <span class="text-sm text-textPrimary group-hover/link:underline">${link.title}</span>
                                </div>
                            </a>`;
                        });
            html += `           </div>
                    </div>
                </div>
            </div>`;
        });
    } else {
        html += `<div class="bg-gcSurface border border-gcBorder rounded-lg p-8 text-center"><p class="text-textSecondary text-sm">No materials posted yet.</p></div>`;
    }

    let themeIndex = ThemeColors.indexOf(theme);
    html += `
                </div>
                <div class="mt-4 flex justify-start">
                    <button onclick="window.App.router.navigate('submit_request', {code: '${data.code}', themeIndex: ${themeIndex}})" class="bg-transparent border border-gcBorder text-gcBlue px-4 py-2 rounded font-medium hover:bg-gcSurface transition text-sm">
                        Raise Material Request
                    </button>
                </div>
            </div>
        </div>
    </div>`;
    return html;
}

export function generateRequestFormHTML(subjectCode, theme) {
    return `
    <div class="max-w-3xl mx-auto fade-in pb-20">
        <button onclick="window.App.router.navigate('subject', {code: '${subjectCode}', themeIndex: ${ThemeColors.indexOf(theme)}})" class="text-textSecondary hover:text-white mb-6 flex items-center gap-2 transition text-sm font-medium">
            <span class="material-symbols-outlined text-sm">arrow_back</span> Back to Subject
        </button>
        
        <div class="${theme.bg} rounded-xl p-8 mb-6 shadow-md relative overflow-hidden">
            <h1 class="text-3xl font-medium text-white relative z-10">Raise Request</h1>
            <p class="text-white opacity-80 mt-2 relative z-10">Subject: ${subjectCode}</p>
        </div>

        <form onsubmit="window.App.submitRequest(event, '${subjectCode}')" class="bg-gcSurface border border-gcBorder rounded-lg p-8 space-y-6 shadow-sm">
            <div>
                <label class="block text-sm text-textSecondary mb-2 font-medium">Query Type</label>
                <select id="req-type" class="w-full bg-gcDark border border-gcBorder rounded p-3 text-textPrimary focus:border-gcBlue focus:outline-none">
                    <option value="New Material">Request New Material</option>
                    <option value="Update Link">Report Broken Link</option>
                    <option value="Bug">System Bug</option>
                </select>
            </div>
            <div>
                <label class="block text-sm text-textSecondary mb-2 font-medium">Title / Description</label>
                <input type="text" id="req-title" maxlength="150" class="w-full bg-gcDark border border-gcBorder rounded p-3 text-textPrimary focus:border-gcBlue focus:outline-none" required placeholder="e.g., Missing Unit 3 PDF">
            </div>
            <div>
                <label class="block text-sm text-textSecondary mb-2 font-medium">Suggested URL (Optional)</label>
                <input type="url" id="req-url" maxlength="255" class="w-full bg-gcDark border border-gcBorder rounded p-3 text-textPrimary focus:border-gcBlue focus:outline-none" placeholder="https://...">
            </div>
            <div class="flex justify-end pt-4">
                <button type="submit" class="bg-gcBlue text-gcDark px-6 py-2 rounded font-medium hover:bg-blue-400 transition shadow-md">Submit to Faculty</button>
            </div>
        </form>
    </div>`;
}

export function generateRequestsPanelHTML(requests, role) {
    let html = `
    <div class="max-w-5xl mx-auto fade-in pb-20">
        <button onclick="window.App.router.navigate('dashboard')" class="text-textSecondary hover:text-white mb-6 flex items-center gap-2 transition text-sm font-medium">
            <span class="material-symbols-outlined text-sm">arrow_back</span> Back to Dashboard
        </button>

        <h2 class="text-3xl font-medium text-white mb-8 border-b border-gcBorder pb-4">Requests Dashboard</h2>`;

    if (role === 'student') {
        html += `<div class="bg-gcSurface border border-gcBorder rounded-lg p-8 text-center text-textSecondary">Students must raise requests directly from the specific Subject Detail page. Tracking coming soon.</div></div>`;
        return html;
    }

    if (!requests || requests.length === 0) {
        html += `<div class="bg-gcSurface border border-gcBorder rounded-lg p-8 text-center text-textSecondary">No pending requests require your attention.</div></div>`;
        return html;
    }

    html += `<div class="space-y-4">`;
    requests.forEach(req => {
        html += `
        <div class="bg-gcSurface border border-gcBorder rounded-lg p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-6 shadow-sm hover:border-gray-500 transition">
            <div class="flex-1">
                <div class="flex items-center gap-3 mb-2">
                    <span class="bg-purple-900/50 text-purple-400 px-2 py-0.5 rounded text-xs font-bold border border-purple-700 tracking-wider">${req.subject_code}</span>
                    <span class="bg-yellow-900/50 text-yellow-400 px-2 py-0.5 rounded text-xs font-bold border border-yellow-700 tracking-wider">${req.status.toUpperCase()}</span>
                </div>
                <h3 class="text-lg font-medium text-textPrimary">${req.link_title}</h3>
                <p class="text-sm text-textSecondary mt-1">Type: ${req.query_type}</p>
                <p class="text-xs text-textSecondary mt-3">Raised by ID: <span class="text-textPrimary">${req.requester_id || req.student_id || 'Unknown'}</span></p>
            </div>
            
            <div class="flex gap-3 shrink-0">
                ${req.link_url ? `<a href="${req.link_url}" target="_blank" class="border border-gcBorder text-textSecondary hover:text-white px-4 py-2 rounded text-sm font-medium transition">Check URL</a>` : ''}
                <button onclick="window.App.ui.showToast('Backend placeholder: Approval logic under construction.', 'info')" class="bg-green-600/80 hover:bg-green-600 text-white px-4 py-2 rounded text-sm font-medium transition">Approve</button>
            </div>
        </div>`;
    });
    html += `</div></div>`;
    return html;
}

export function generateEditModalHTML(subjects) {
    let subjectOptions = subjects.map(sub => `<option value="${sub.subject_code}">${sub.subject_code} - ${sub.subject_name || ''}</option>`).join('');
    
    return `
    <div class="flex justify-between items-center mb-6">
        <h2 class="text-2xl font-medium text-white flex items-center gap-2"><span class="material-symbols-outlined text-gcBlue">edit</span> Edit Material Link</h2>
        <button onclick="window.App.closeModal()" class="text-textSecondary hover:text-white transition text-xl"><span class="material-symbols-outlined">close</span></button>
    </div>
    <form onsubmit="window.App.submitRequest(event, null, 'Update Link')" class="space-y-4">
        <div>
            <label class="block text-sm text-textSecondary mb-2">Select Subject</label>
            <select id="req-subject" class="w-full bg-gcDark border border-gcBorder rounded p-3 text-textPrimary focus:border-gcBlue focus:outline-none" required>
                ${subjectOptions}
            </select>
        </div>
        <div>
            <label class="block text-sm text-textSecondary mb-2">Link Title to Edit</label>
            <input type="text" id="req-title" maxlength="150" class="w-full bg-gcDark border border-gcBorder rounded p-3 text-textPrimary focus:border-gcBlue focus:outline-none" required placeholder="e.g., Unit 1 Notes">
        </div>
        <div>
            <label class="block text-sm text-textSecondary mb-2">New Correct URL</label>
            <input type="url" id="req-url" maxlength="255" class="w-full bg-gcDark border border-gcBorder rounded p-3 text-textPrimary focus:border-gcBlue focus:outline-none" required placeholder="https://...">
        </div>
        <div class="flex justify-end pt-4 gap-3">
            <button type="button" onclick="window.App.closeModal()" class="px-4 py-2 text-textSecondary hover:text-white transition">Cancel</button>
            <button type="submit" class="bg-gcBlue text-gcDark px-6 py-2 rounded font-medium hover:bg-blue-400 transition shadow-md">Submit Correction</button>
        </div>
    </form>`;
}
