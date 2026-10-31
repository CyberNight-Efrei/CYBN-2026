
async function loadWallet() {
    try {
        const response = await fetch("/api/wallet");
        const wallet = await response.json();

        document.getElementById("balance").textContent =
            wallet.balance;

        const ticketsList = document.getElementById("tickets-list");
        ticketsList.replaceChildren();

        if (wallet.tickets.length === 0) {
            ticketsList.textContent = "Aucun billet acheté.";
            return;
        }

        wallet.tickets.forEach(ticket => {
            const item = document.createElement("div");
            item.className = "my-ticket";

            const info = document.createElement("div");
            info.className = "my-ticket-info";

            const name = document.createElement("strong");
            name.textContent =
                `#${ticket.id} — ${ticket.type.toUpperCase()}`;

            const details = document.createElement("span");
            details.textContent =
                `${ticket.price} crédits · ${
                    ticket.status === "refunded"
                        ? "Remboursé"
                        : "Actif"
                }`;

            info.appendChild(name);
            info.appendChild(details);
            item.appendChild(info);

            if (
                ticket.type === "standard" &&
                ticket.status === "active"
            ) {
                const button = document.createElement("button");

                button.className = "btn btn-refund";
                button.textContent = "Rembourser";

                button.addEventListener("click", async () => {
                    button.disabled = true;
                    await refundTicket(ticket.id);
                });

                item.appendChild(button);
            }

            if (ticket.status === "refunded") {
                const badge = document.createElement("span");
                badge.className = "refunded-badge";
                badge.textContent = "✓ Remboursé";
                item.appendChild(badge);
            }

            ticketsList.appendChild(item);
        });

    } catch (error) {
        showMessage(
            "Impossible de charger le portefeuille.",
            false
        );
    }
}


// ==========================================
// ACHAT DE BILLETS
// ==========================================

async function buyTicket(ticketType) {
    try {
        const response = await fetch("/api/buy", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                ticket_type: ticketType
            })
        });

        const result = await response.json();

        showMessage(result.message, result.success);
        await loadWallet();

    } catch (error) {
        showMessage(
            "Erreur de communication avec le serveur.",
            false
        );
    }
}


// ==========================================
// REMBOURSEMENT
// ==========================================

async function refundTicket(ticketId) {
    try {
        const response = await fetch("/api/refund", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                ticket_id: ticketId
            })
        });

        const result = await response.json();

        showMessage(result.message, result.success);
        await loadWallet();

    } catch (error) {
        showMessage(
            "Impossible de rembourser ce billet.",
            false
        );
        await loadWallet();
    }
}


// ==========================================
// NOTIFICATIONS TOAST
// ==========================================

function showMessage(message, success) {
    const container = document.getElementById("toast-container");

    const toast = document.createElement("div");
    toast.className = `toast ${success ? "success" : "error"}`;
    toast.setAttribute("role", success ? "status" : "alert");

    const icon = document.createElement("span");
    icon.className = "toast-icon";
    icon.textContent = success ? "✓" : "⚠";

    const content = document.createElement("div");
    content.className = "toast-content";

    const title = document.createElement("div");
    title.className = "toast-title";
    title.textContent = success
        ? "Opération réussie"
        : "Opération refusée";

    const description = document.createElement("div");
    description.className = "toast-message";
    description.textContent = message;

    const close = document.createElement("button");
    close.className = "toast-close";
    close.textContent = "×";
    close.setAttribute(
        "aria-label",
        "Fermer la notification"
    );

    function dismissToast() {
        if (toast.classList.contains("hide")) return;

        toast.classList.add("hide");
        setTimeout(() => toast.remove(), 250);
    }

    close.addEventListener("click", dismissToast);

    content.appendChild(title);
    content.appendChild(description);

    toast.appendChild(icon);
    toast.appendChild(content);
    toast.appendChild(close);

    container.appendChild(toast);

    setTimeout(dismissToast, 4000);
}


// ==========================================
// INITIALISATION
// ==========================================

document.addEventListener("DOMContentLoaded", loadWallet);
