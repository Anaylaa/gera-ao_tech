
const API_URL = "";

const state = {
    livros: [],
    leitores: [],
    emprestimos: []
};

const $ = (selector) => document.querySelector(selector);

const CATEGORIAS = [
    "Literatura",
    "Ficção",
    "História",
    "Filosofia",
    "Ciências Exatas",
    "Ciências Biológicas",
    "Tecnologia",
    "Artes",
    "Ciências Sociais"
];

/* CATEGORIAS */

function preencherCategorias() {
    const filtro = $("#filterCategory");
    const cadastro = $("#bookCategory");

    if (filtro) {
        filtro.innerHTML = `
            <option value="">Todas as categorias</option>
            ${CATEGORIAS.map(categoria =>
                `<option value="${escapeHTML(categoria)}">${escapeHTML(categoria)}</option>`
            ).join("")}
        `;
    }

    if (cadastro) {
        cadastro.innerHTML = `
            <option value="">Selecione uma categoria</option>
            ${CATEGORIAS.map(categoria =>
                `<option value="${escapeHTML(categoria)}">${escapeHTML(categoria)}</option>`
            ).join("")}
        `;
    }
}

/* FUNÇÕES AUXILIARES */

const money = (value) =>
    Number(value || 0).toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL"
    });

const date = (value) => {
    if (!value) return "—";

    const parsed = new Date(
        value + (value.length === 10 ? "T00:00:00" : "")
    );

    if (Number.isNaN(parsed.getTime())) return "—";

    return parsed.toLocaleDateString("pt-BR");
};

const escapeHTML = (value) =>
    String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[char]);

function showToast(message, error = false) {
    const toast = $("#toast");

    toast.textContent = message;
    toast.style.borderLeftColor = error ? "#d16c62" : "#b99a5b";
    toast.classList.add("show");

    setTimeout(() => toast.classList.remove("show"), 3500);
}

/* COMUNICAÇÃO COM A API - ATUALIZADA */

async function api(path, options = {}) {
    const config = {
        ...options,
        headers: {
            ...(options.body
                ? { "Content-Type": "application/json" }
                : {}),
            ...options.headers
        }
    };

    let response;

    try {
        response = await fetch(`${API_URL}${path}`, config);
    } catch (error) {
        console.error(`Erro de conexão em ${path}:`, error);

        throw new Error(
            `Não foi possível conectar ao servidor: ${path}`
        );
    }

    const responseText = await response.text();

    let data = null;

    try {
        data = responseText ? JSON.parse(responseText) : null;
    } catch {
        data = responseText;
    }

    if (!response.ok) {
        console.error("Erro na API:", {
            rota: path,
            status: response.status,
            resposta: data
        });

        const detail = typeof data === "object" && data !== null
            ? data.detail || JSON.stringify(data)
            : data;

        throw new Error(
            `Erro ${response.status} em ${path}: ${detail || "Sem detalhes"}`
        );
    }

    return data;
}

/* NAVEGAÇÃO */

function navigate(pageName) {
    document.querySelectorAll(".page").forEach(page => {
        page.classList.toggle("active", page.id === pageName);
    });

    document.querySelectorAll(".nav-item").forEach(button => {
        button.classList.toggle(
            "active",
            button.dataset.page === pageName
        );
    });

    const activeButton = document.querySelector(
        `.nav-item[data-page="${pageName}"]`
    );

    $("#pageTitle").textContent = activeButton
        ? activeButton.textContent.trim()
        : "Visão geral";

    $("#sidebar").classList.remove("open");

    if (pageName === "dashboard") renderDashboard();
    if (pageName === "livros") renderBooks();
    if (pageName === "leitores") renderReaders();
    if (pageName === "emprestimos") renderLoans();
    if (pageName === "devolucoes") renderReturns();
    if (pageName === "multas") renderFines();
    if (pageName === "relatorios") renderReports();
}

document.querySelectorAll(".nav-item").forEach(button => {
    button.addEventListener("click", () => navigate(button.dataset.page));
});

document.querySelectorAll("[data-go]").forEach(button => {
    button.addEventListener("click", () => navigate(button.dataset.go));
});

$("#mobileMenu").addEventListener("click", () => {
    $("#sidebar").classList.toggle("open");
});

/* MODAIS */

function openModal(id) {
    $(`#${id}`).classList.add("open");
}

function closeModal(id) {
    $(`#${id}`).classList.remove("open");
}

document.querySelectorAll("[data-close]").forEach(button => {
    button.addEventListener("click", () =>
        closeModal(button.dataset.close)
    );
});

document.querySelectorAll(".modal-overlay").forEach(modal => {
    modal.addEventListener("click", event => {
        if (event.target === modal) {
            modal.classList.remove("open");
        }
    });
});

$("#openBookModal").addEventListener("click", () =>
    openModal("bookModal")
);

$("#openReaderModal").addEventListener("click", () =>
    openModal("readerModal")
);

$("#openLoanModal").addEventListener("click", () => {
    populateLoanOptions();
    openModal("loanModal");
});

/* CARREGAMENTO DOS DADOS */

async function loadData() {
    try {
        const [livros, leitores, emprestimos] = await Promise.all([
            api("/livros"),
            api("/leitores"),
            api("/emprestimos")
        ]);

        if (!Array.isArray(livros)) {
            throw new Error("A rota /livros não retornou uma lista.");
        }

        if (!Array.isArray(leitores)) {
            throw new Error("A rota /leitores não retornou uma lista.");
        }

        if (!Array.isArray(emprestimos)) {
            throw new Error("A rota /emprestimos não retornou uma lista.");
        }

        state.livros = livros;
        state.leitores = leitores;
        state.emprestimos = emprestimos;

        renderDashboard();
        renderBooks();
        renderReaders();
        renderLoans();
        renderReturns();
        renderFines();
        renderReports();

    } catch (error) {
        console.error("Erro ao carregar os dados:", error);
        showToast(error.message, true);
    }
}

/* IDENTIFICAÇÃO DE LIVROS E LEITORES */

function getBookName(loan) {
    const book = state.livros.find(
        item => item.id === loan.livro_id
    );

    return book ? book.titulo : `Livro #${loan.livro_id}`;
}

function getReaderName(loan) {
    const reader = state.leitores.find(
        item => item.id === loan.leitor_id
    );

    return reader ? reader.nome : `Leitor #${loan.leitor_id}`;
}

function getLoanStatus(loan) {
    if (loan.status !== "ativo") return loan.status;

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const dueDate = new Date(
        `${loan.data_devolucao_prevista}T00:00:00`
    );

    return dueDate < today ? "overdue" : "active";
}

function loanBadge(loan) {
    const status = getLoanStatus(loan);

    if (status === "overdue") {
        return `<span class="badge badge-red">Atrasado</span>`;
    }

    if (status === "active" || status === "ativo") {
        return `<span class="badge badge-green">Ativo</span>`;
    }

    return `<span class="badge badge-gray">Devolvido</span>`;
}

function tableTemplate(headers, rows) {
    if (!rows.length) {
        return `<p class="empty-state">Nenhum registro encontrado.</p>`;
    }

    return `
        <table>
            <thead>
                <tr>
                    ${headers.map(header => `<th>${header}</th>`).join("")}
                </tr>
            </thead>
            <tbody>
                ${rows.join("")}
            </tbody>
        </table>
    `;
}

/* DASHBOARD */

function renderDashboard() {
    const total = state.livros.reduce(
        (sum, book) => sum + Number(book.quantidade_total || 0),
        0
    );

    const readers = state.leitores.length;

    const activeLoans = state.emprestimos.filter(
        loan => loan.status === "ativo"
    );

    const pendingFines = state.emprestimos.filter(
        loan => Number(loan.multa || 0) > 0 &&
            loan.status_multa !== "paga"
    );

    const fineTotal = pendingFines.reduce(
        (sum, loan) => sum + Number(loan.multa || 0),
        0
    );

    $("#totalLivros").textContent = total;
    $("#totalLeitores").textContent = readers;
    $("#totalAtivos").textContent = activeLoans.length;
    $("#totalMultas").textContent = pendingFines.length;
    $("#valorMultas").textContent = money(fineTotal);

    const recent = [...state.emprestimos]
        .sort((a, b) => b.id - a.id)
        .slice(0, 5);

    const recentRows = recent.map(loan => `
        <tr>
            <td>#${loan.id}</td>
            <td>${escapeHTML(getBookName(loan))}</td>
            <td>${escapeHTML(getReaderName(loan))}</td>
            <td>${date(loan.data_emprestimo)}</td>
            <td>${loanBadge(loan)}</td>
        </tr>
    `);

    $("#recentLoans").innerHTML = tableTemplate(
        ["ID", "Livro", "Leitor", "Data", "Situação"],
        recentRows
    );

    const upcoming = [...activeLoans]
        .sort((a, b) =>
            new Date(a.data_devolucao_prevista) -
            new Date(b.data_devolucao_prevista)
        )
        .slice(0, 5);

    $("#upcomingLoans").innerHTML = upcoming.length
        ? upcoming.map(loan => `
            <div class="upcoming-item">
                <div>
                    <strong>${escapeHTML(getBookName(loan))}</strong>
                    <small>${escapeHTML(getReaderName(loan))}</small>
                </div>
                <span>${date(loan.data_devolucao_prevista)}</span>
            </div>
        `).join("")
        : `<p class="empty-state">Nenhum empréstimo ativo.</p>`;
}

$("#refreshDashboard").addEventListener("click", loadData);

/* LIVROS */

function renderBooks() {
    const search = ($("#searchBooks")?.value || "").toLowerCase();
    const category = $("#filterCategory")?.value || "";

    const books = state.livros.filter(book => {
        const text = [
            book.titulo,
            book.autor,
            book.isbn
        ].join(" ").toLowerCase();

        return text.includes(search) &&
            (!category || book.categoria === category);
    });

    $("#booksGrid").innerHTML = books.length
        ? books.map(book => `
            <article class="book-card">
                <div class="book-cover">L</div>
                <div class="book-info">
                    <h3>${escapeHTML(book.titulo)}</h3>
                    <p>${escapeHTML(book.autor)}</p>
                    <p>${escapeHTML(book.categoria)}</p>
                    <small>ISBN: ${escapeHTML(book.isbn)}</small>
                    <small>
                        Disponíveis: ${book.quantidade_disponivel}
                        / ${book.quantidade_total}
                    </small>
                </div>
            </article>
        `).join("")
        : `<p class="empty-state">Nenhum livro encontrado.</p>`;
}

$("#searchBooks").addEventListener("input", renderBooks);
$("#filterCategory").addEventListener("change", renderBooks);

/* CADASTRO DE LIVROS */

$("#bookForm").addEventListener("submit", async event => {
    event.preventDefault();

    const form = new FormData(event.target);

    const data = {
        titulo: form.get("titulo").trim(),
        autor: form.get("autor").trim(),
        isbn: form.get("isbn").trim(),
        categoria: form.get("categoria").trim(),
        quantidade_total: Number(form.get("quantidade_total"))
    };

    try {
        await api("/livros", {
            method: "POST",
            body: JSON.stringify(data)
        });

        event.target.reset();
        closeModal("bookModal");
        showToast("Livro cadastrado com sucesso!");

        await loadData();

    } catch (error) {
        showToast(error.message, true);
    }
});

/* LEITORES */

function renderReaders() {
    const search = ($("#searchReaders")?.value || "").toLowerCase();

    const readers = state.leitores.filter(reader =>
        `${reader.nome} ${reader.email}`.toLowerCase().includes(search)
    );

    const rows = readers.map(reader => `
        <tr>
            <td><strong>${escapeHTML(reader.nome)}</strong></td>
            <td>${escapeHTML(reader.email)}</td>
            <td>${escapeHTML(reader.telefone || "—")}</td>
            <td>${date(reader.data_cadastro)}</td>
        </tr>
    `);

    $("#readersTable").innerHTML = tableTemplate(
        ["Nome", "E-mail", "Telefone", "Cadastro"],
        rows
    );
}

$("#searchReaders").addEventListener("input", renderReaders);

/* CADASTRO DE LEITORES */

$("#readerForm").addEventListener("submit", async event => {
    event.preventDefault();

    const form = new FormData(event.target);

    const data = {
        nome: form.get("nome").trim(),
        email: form.get("email").trim(),
        telefone: form.get("telefone").trim() || null
    };

    try {
        await api("/leitores", {
            method: "POST",
            body: JSON.stringify(data)
        });

        event.target.reset();
        closeModal("readerModal");
        showToast("Leitor cadastrado com sucesso!");

        await loadData();

    } catch (error) {
        showToast(error.message, true);
    }
});

/* EMPRÉSTIMOS */

function populateLoanOptions() {
    const availableBooks = state.livros.filter(
        book => Number(book.quantidade_disponivel) > 0
    );

    $("#loanBook").innerHTML = `
        <option value="">Selecione um livro</option>
        ${availableBooks.map(book => `
            <option value="${book.id}">
                ${escapeHTML(book.titulo)} — ${book.quantidade_disponivel} disponível(is)
            </option>
        `).join("")}
    `;

    $("#loanReader").innerHTML = `
        <option value="">Selecione um leitor</option>
        ${state.leitores.map(reader => `
            <option value="${reader.id}">
                ${escapeHTML(reader.nome)}
            </option>
        `).join("")}
    `;
}

function renderLoans() {
    const search = ($("#searchLoans")?.value || "").toLowerCase();
    const status = $("#filterLoanStatus")?.value || "";

    const loans = state.emprestimos.filter(loan => {
        const text = `${getBookName(loan)} ${getReaderName(loan)}`.toLowerCase();

        return text.includes(search) &&
            (!status || loan.status === status);
    });

    const rows = loans.map(loan => `
        <tr>
            <td>#${loan.id}</td>
            <td><strong>${escapeHTML(getBookName(loan))}</strong></td>
            <td>${escapeHTML(getReaderName(loan))}</td>
            <td>${date(loan.data_emprestimo)}</td>
            <td>${date(loan.data_devolucao_prevista)}</td>
            <td>${loanBadge(loan)}</td>
            <td>
                ${loan.status === "ativo" && loan.renovacoes < 5
                    ? `<button class="table-action" data-renew="${loan.id}">Renovar</button>`
                    : "—"}
            </td>
        </tr>
    `);

    $("#loansTable").innerHTML = tableTemplate(
        ["ID", "Livro", "Leitor", "Data", "Prazo", "Situação", "Ação"],
        rows
    );
}

$("#searchLoans").addEventListener("input", renderLoans);
$("#filterLoanStatus").addEventListener("change", renderLoans);

/* CADASTRO DE EMPRÉSTIMOS */

$("#loanForm").addEventListener("submit", async event => {
    event.preventDefault();

    const form = new FormData(event.target);

    const data = {
        livro_id: Number(form.get("livro_id")),
        leitor_id: Number(form.get("leitor_id"))
    };

    try {
        await api("/emprestimos", {
            method: "POST",
            body: JSON.stringify(data)
        });

        event.target.reset();
        closeModal("loanModal");
        showToast("Empréstimo registrado com sucesso!");

        await loadData();

    } catch (error) {
        showToast(error.message, true);
    }
});

/* RENOVAÇÃO */

$("#loansTable").addEventListener("click", async event => {
    const button = event.target.closest("[data-renew]");

    if (!button) return;

    const id = button.dataset.renew;

    if (!confirm("Deseja renovar este empréstimo por mais 30 dias?")) {
        return;
    }

    try {
        await api(`/emprestimos/${id}/renovacao`, {
            method: "POST"
        });

        showToast("Empréstimo renovado com sucesso!");
        await loadData();

    } catch (error) {
        showToast(error.message, true);
    }
});

/* DEVOLUÇÕES */

function renderReturns() {
    const activeLoans = state.emprestimos.filter(
        loan => loan.status === "ativo"
    );

    const rows = activeLoans.map(loan => `
        <tr>
            <td>#${loan.id}</td>
            <td><strong>${escapeHTML(getBookName(loan))}</strong></td>
            <td>${escapeHTML(getReaderName(loan))}</td>
            <td>${date(loan.data_devolucao_prevista)}</td>
            <td>${loanBadge(loan)}</td>
            <td>
                <button class="table-action" data-return="${loan.id}">
                    Registrar devolução
                </button>
            </td>
        </tr>
    `);

    $("#returnsTable").innerHTML = tableTemplate(
        ["ID", "Livro", "Leitor", "Prazo", "Situação", "Ação"],
        rows
    );
}

/* REGISTRAR DEVOLUÇÃO */

$("#returnsTable").addEventListener("click", async event => {
    const button = event.target.closest("[data-return]");

    if (!button) return;

    const id = button.dataset.return;

    if (!confirm("Confirmar a devolução deste livro?")) {
        return;
    }

    try {
        await api(`/emprestimos/${id}/devolucao`, {
            method: "POST"
        });

        showToast("Devolução registrada com sucesso!");
        await loadData();

    } catch (error) {
        showToast(error.message, true);
    }
});

/* MULTAS */

function renderFines() {
    const fines = state.emprestimos.filter(
        loan => Number(loan.multa || 0) > 0
    );

    const pending = fines.filter(
        loan => loan.status_multa !== "paga"
    );

    const paid = fines.filter(
        loan => loan.status_multa === "paga"
    );

    const pendingValue = pending.reduce(
        (sum, loan) => sum + Number(loan.multa || 0),
        0
    );

    $("#pendingFineCount").textContent = pending.length;
    $("#pendingFineValue").textContent = money(pendingValue);
    $("#paidFineCount").textContent = paid.length;

    const rows = fines.map(loan => `
        <tr>
            <td>#${loan.id}</td>
            <td>${escapeHTML(getBookName(loan))}</td>
            <td>${escapeHTML(getReaderName(loan))}</td>
            <td>${money(loan.multa)}</td>
            <td>
                ${loan.status_multa === "paga"
                    ? `<span class="badge badge-green">Paga</span>`
                    : `<span class="badge badge-red">Pendente</span>`}
            </td>
            <td>
                ${loan.status_multa !== "paga"
                    ? `<button class="table-action" data-pay-fine="${loan.id}">Registrar pagamento</button>`
                    : date(loan.data_pagamento_multa)}
            </td>
        </tr>
    `);

    $("#finesTable").innerHTML = tableTemplate(
        ["Empréstimo", "Livro", "Leitor", "Valor", "Situação", "Ação"],
        rows
    );
}

/* PAGAMENTO DE MULTAS */

$("#finesTable").addEventListener("click", async event => {
    const button = event.target.closest("[data-pay-fine]");

    if (!button) return;

    const id = button.dataset.payFine;

    if (!confirm("Confirmar o pagamento desta multa?")) {
        return;
    }

    try {
        await api(`/emprestimos/${id}/pagamento-multa`, {
            method: "POST"
        });

        showToast("Pagamento registrado com sucesso!");
        await loadData();

    } catch (error) {
        showToast(error.message, true);
    }
});

/* RELATÓRIOS */

function renderReports() {
    const total = state.livros.reduce(
        (sum, book) => sum + Number(book.quantidade_total || 0),
        0
    );

    const available = state.livros.reduce(
        (sum, book) => sum + Number(book.quantidade_disponivel || 0),
        0
    );

    const borrowed = total - available;

    const overdue = state.emprestimos.filter(
        loan => loan.status === "ativo" &&
            getLoanStatus(loan) === "overdue"
    ).length;

    const occupancy = total > 0
        ? (borrowed / total) * 100
        : 0;

    $("#reportAvailable").textContent = available;
    $("#reportBorrowed").textContent = borrowed;
    $("#reportOverdue").textContent = overdue;
    $("#reportOccupancy").textContent = `${occupancy.toFixed(1)}%`;

    const categories = {};

    state.livros.forEach(book => {
        const category = book.categoria || "Sem categoria";

        categories[category] =
            (categories[category] || 0) +
            Number(book.quantidade_total || 0);
    });

    const max = Math.max(...Object.values(categories), 1);

    $("#categoryReport").innerHTML = Object.entries(categories).length
        ? Object.entries(categories).map(([name, quantity]) => `
            <div class="category-row">
                <span>${escapeHTML(name)}</span>
                <div class="category-bar">
                    <div class="category-fill"
                        style="width: ${(quantity / max) * 100}%">
                    </div>
                </div>
                <strong>${quantity}</strong>
            </div>
        `).join("")
        : `<p class="empty-state">Ainda não existem categorias cadastradas.</p>`;
}

/* EXPORTAÇÃO DE RELATÓRIO */

$("#exportReport").addEventListener("click", () => {
    const header = [
        "ID",
        "Livro",
        "Leitor",
        "Data do emprestimo",
        "Data prevista de devolucao",
        "Data real de devolucao",
        "Status",
        "Multa",
        "Status da multa"
    ];

    const rows = state.emprestimos.map(loan => [
        loan.id,
        getBookName(loan),
        getReaderName(loan),
        loan.data_emprestimo,
        loan.data_devolucao_prevista,
        loan.data_devolucao_real || "",
        loan.status,
        loan.multa,
        loan.status_multa
    ]);

    const csv = [header, ...rows]
        .map(row => row.map(value =>
            `"${String(value ?? "").replace(/"/g, '""')}"`
        ).join(";"))
        .join("\n");

    const blob = new Blob(
        ["\uFEFF" + csv],
        { type: "text/csv;charset=utf-8;" }
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "relatorio-libratech.csv";
    link.click();

    URL.revokeObjectURL(url);
});

/* INICIALIZAÇÃO */

preencherCategorias();
loadData();
