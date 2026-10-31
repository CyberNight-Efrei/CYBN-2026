
 // ==========================================
 // PORTEFEUILLE ET BILLETS
 // ==========================================

async function loadWallet() {
    try {
        const response = await fetch("/api/wallet");

        if (!response.ok) {
            throw new Error("Erreur lors du chargement.");
        }

        const wallet = await response.json();

        document.getElementById("balance").textContent =
            wallet.balance;

        const ticketsList = document.getElementById("tickets-list");
        ticketsList.replaceChildren();

        if (wallet.tickets.length === 0) {
            ticketsList.textContent = "Aucun billet acheté.";
        } else {
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

                // Bouton remboursement :
                // uniquement pour les billets Standard actifs.
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

                // Badge des billets remboursés.
                if (ticket.status === "refunded") {
                    const badge = document.createElement("span");
                    badge.className = "refunded-badge";
                    badge.textContent = "✓ Remboursé";
                    item.appendChild(badge);
                }

                ticketsList.appendChild(item);
            });
        }

        // Vérifier la récompense après chaque
        // actualisation du portefeuille.
        await loadReward();

    } catch (error) {
        console.error("Erreur portefeuille :", error);

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

        // Recharge le solde et les billets.
        // Si le VIP a été acheté, le flag apparaît.
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
// RÉCOMPENSE VIP
// ==========================================

async function loadReward() {
    const rewardSection = document.getElementById("vip-reward");
    const flagElement = document.getElementById("vip-flag");

    if (!rewardSection || !flagElement) {
        return;
    }

    // Masquer le flag tant que le serveur
    // n'a pas confirmé l'accès VIP.
    rewardSection.hidden = true;
    flagElement.textContent = "";

    try {
        const response = await fetch("/api/reward");
        const result = await response.json();

        if (!response.ok || !result.success) {
            return;
        }

        // Affichage sécurisé : textContent
        // n'interprète pas le flag comme du HTML.
        flagElement.textContent = result.flag;
        rewardSection.hidden = false;

    } catch (error) {
        console.error(
            "Impossible de charger la récompense :",
            error
        );
    }
}


// ==========================================
// COPIE DU FLAG
// ==========================================

async function copyFlag() {
    const flag = document.getElementById("vip-flag")?.textContent;

    if (!flag) {
        showMessage("Aucun flag disponible.", false);
        return;
    }

    try {
        await navigator.clipboard.writeText(flag);

        showMessage(
            "Flag copié dans le presse-papiers !",
            true
        );

    } catch (error) {
        showMessage(
            "Impossible de copier le flag.",
            false
        );
    }
}


// ==========================================
// NOTIFICATIONS TOAST
// ==========================================

function showMessage(message, success) {
    const container = document.getElementById("toast-container");

    if (!container) {
        console.warn("Notification :", message);
        return;
    }

    const toast = document.createElement("div");
    toast.className = `toast ${success ? "success" : "error"}`;

    toast.setAttribute(
        "role",
        success ? "status" : "alert"
    );

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
        if (toast.classList.contains("hide")) {
            return;
        }

        toast.classList.add("hide");

        setTimeout(() => {
            toast.remove();
        }, 250);
    }

    close.addEventListener("click", dismissToast);

    content.appendChild(title);
    content.appendChild(description);

    toast.appendChild(icon);
    toast.appendChild(content);
    toast.appendChild(close);

    container.appendChild(toast);

    // Disparition automatique après 4 secondes.
    setTimeout(dismissToast, 4000);
}


// ==========================================
// INITIALISATION DE L'APPLICATION
// ==========================================

document.addEventListener("DOMContentLoaded", async () => {

    // Charger le portefeuille et vérifier
    // automatiquement l'accès VIP.
    await loadWallet();

    // Activer le bouton de copie du flag.
    const copyButton = document.getElementById("copy-flag");

    if (copyButton) {
        copyButton.addEventListener("click", copyFlag);
    }

});
