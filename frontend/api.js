export async function callBackend(action, args = []) {
    try {
        const response = await fetch('/api', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: action,
                args: args
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
        
    } catch (error) {
        console.error("API Communication Error:", error);
        return { 
            status: "error", 
            message: "Network Error: Could not reach the backend server.", 
            payload: null 
        };
    }
}
