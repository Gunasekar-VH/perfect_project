const STORAGE_KEY = 'library_static_data_v1';
const SESSION_KEY = 'library_static_session_v1';
const LOAN_DAYS = 14;

const $ = (id) => document.getElementById(id);
const state = { user: null, books: [], loans: [], users: [] };
const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (character) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;',
})[character]);
const serializeData = (value) => encodeURIComponent(JSON.stringify(value));
const getFormData = (form) => Object.fromEntries(new FormData(form).entries());
const timestamp = () => new Date().toISOString();
const dateString = (date = new Date()) => date.toISOString().slice(0, 10);

function createLibraryData() {
  const createdAt = timestamp();
  return {
    users: [{ id: 1, name: 'Administrator', email: 'admin@library.local', password: 'admin123', role: 'admin', created_at: createdAt }],
    books: [
      { id: 1, title: 'The Pragmatic Programmer', author: 'Andy Hunt', isbn: '9780201616224', category: 'Programming', description: 'Classic software craftsmanship guide.', total_copies: 3, created_at: createdAt, updated_at: createdAt },
      { id: 2, title: 'Clean Code', author: 'Robert C. Martin', isbn: '9780132350884', category: 'Programming', description: 'Practices for readable, maintainable code.', total_copies: 4, created_at: createdAt, updated_at: createdAt },
      { id: 3, title: 'Designing Data-Intensive Applications', author: 'Martin Kleppmann', isbn: '9781449373320', category: 'Databases', description: 'Modern data systems concepts.', total_copies: 2, created_at: createdAt, updated_at: createdAt },
      { id: 4, title: 'The Alchemist', author: 'Paulo Coelho', isbn: '9780061122415', category: 'Fiction', description: 'A novel about purpose and journey.', total_copies: 5, created_at: createdAt, updated_at: createdAt },
    ],
    loans: [],
  };
}

function loadStore() {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (stored && Array.isArray(stored.users) && Array.isArray(stored.books) && Array.isArray(stored.loans)) return stored;
  } catch {
    // Start with a fresh demo library if a browser has malformed saved data.
  }
  const initialData = createLibraryData();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(initialData));
  return initialData;
}

let store = loadStore();

function saveStore() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
}

function nextId(records) {
  return Math.max(0, ...records.map((record) => Number(record.id) || 0)) + 1;
}

function activeLoanCount(bookId) {
  return store.loans.filter((loan) => loan.book_id === bookId && !loan.returned_at).length;
}

function withAvailability(book) {
  const available = Math.max(0, Number(book.total_copies) - activeLoanCount(book.id));
  return { ...book, available_copies: available, is_available: available > 0 };
}

function currentUser() {
  const userId = Number(localStorage.getItem(SESSION_KEY));
  return store.users.find((user) => user.id === userId) || null;
}

function toast(message) {
  const element = $('toast');
  element.textContent = message;
  element.classList.remove('hidden');
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => element.classList.add('hidden'), 2800);
}

function loanStatus(loan) {
  if (loan.returned_at) return 'Returned';
  return loan.due_date < dateString() ? 'Overdue' : 'Active';
}

function renderStats() {
  $('bookCount').textContent = state.books.length;
  $('loanCount').textContent = state.loans.filter((loan) => !loan.returned_at).length;
  $('userCount').textContent = state.user?.role === 'admin' ? state.users.length : 0;
}

function renderBooks() {
  const query = $('bookSearch').value.toLowerCase();
  const books = state.books.filter((book) => [book.title, book.author, book.category, book.isbn].join(' ').toLowerCase().includes(query));
  const isAdmin = state.user?.role === 'admin';
  const canBorrow = state.user?.role === 'user';
  $('booksGrid').innerHTML = books.map((book) => `
    <article class="card">
      <div class="badge">${book.is_available ? 'Available' : 'Checked out'} · ${book.available_copies}/${book.total_copies}</div>
      <h3>${escapeHtml(book.title)}</h3>
      <p class="meta">${escapeHtml(book.author)}${book.category ? ` · ${escapeHtml(book.category)}` : ''}</p>
      <p>${escapeHtml(book.description || 'No description provided.')}</p>
      <small>ISBN: ${escapeHtml(book.isbn || 'N/A')}</small>
      <div class="actions">
        ${canBorrow ? `<button ${book.is_available ? '' : 'disabled'} data-borrow="${book.id}">Borrow</button>` : ''}
        ${isAdmin ? `<button class="ghost" data-edit-book="${serializeData(book)}">Edit</button>` : ''}
        ${isAdmin ? `<button class="ghost danger" data-delete-book="${book.id}">Delete</button>` : ''}
      </div>
    </article>`).join('') || '<p>No books found.</p>';
}

function loanRow(loan) {
  const borrower = store.users.find((user) => user.id === loan.user_id);
  const borrowerInfo = state.user?.role === 'admin' && borrower
    ? `<small>${escapeHtml(borrower.name)} · ${escapeHtml(borrower.email)}</small><br>`
    : '';
  return `
    <div class="row">
      <div><strong>${escapeHtml(loan.book_title)}</strong><br>${borrowerInfo}<small>${loanStatus(loan)}</small></div>
      <div><small>Borrowed</small><br>${escapeHtml(loan.borrowed_at)}</div>
      <div><small>Due</small><br>${escapeHtml(loan.due_date)}</div>
      <div class="actions">${loan.returned_at ? '' : `<button data-return="${loan.id}">Return</button>`}</div>
    </div>`;
}

function renderLoans() {
  const rows = state.loans.map(loanRow).join('') || '<p>No loans yet.</p>';
  $('loansList').innerHTML = rows;
  $('adminLoansList').innerHTML = rows;
}

function renderUsers() {
  $('usersList').innerHTML = state.users.map((user) => `
    <div class="row">
      <div><strong>${escapeHtml(user.name)}</strong><br><small>${escapeHtml(user.email)}</small></div>
      <div><small>Role</small><br>${escapeHtml(user.role)}</div>
      <div><small>Joined</small><br>${escapeHtml(user.created_at)}</div>
      <div class="actions">
        <button class="ghost" data-edit-user="${serializeData(user)}">Edit</button>
        ${user.role !== 'admin' ? `<button class="ghost danger" data-delete-user="${user.id}">Delete</button>` : ''}
      </div>
    </div>`).join('') || '<p>No users found.</p>';
}

function loadData() {
  store = loadStore();
  state.user = currentUser();
  state.books = store.books.map(withAvailability).sort((a, b) => a.title.localeCompare(b.title));
  state.users = state.user?.role === 'admin' ? [...store.users].sort((a, b) => b.id - a.id) : [];
  state.loans = state.user
    ? store.loans
      .filter((loan) => state.user.role === 'admin' || loan.user_id === state.user.id)
      .map((loan) => ({ ...loan, book_title: store.books.find((book) => book.id === loan.book_id)?.title || 'Deleted book' }))
      .sort((a, b) => Number(Boolean(a.returned_at)) - Number(Boolean(b.returned_at)) || a.due_date.localeCompare(b.due_date))
    : [];
  $('sessionInfo').textContent = state.user ? `${state.user.name} (${state.user.role})` : 'Not signed in';
  $('adminPanel').classList.toggle('hidden', state.user?.role !== 'admin');
  $('loanHint').textContent = state.user ? (state.user.role === 'admin' ? 'All active and past loans' : 'Your active and past loans') : 'Sign in to view loans';
  renderBooks();
  renderLoans();
  renderUsers();
  renderStats();
}

function addDays(days) {
  const due = new Date();
  due.setDate(due.getDate() + days);
  return dateString(due);
}

$('loginForm').addEventListener('submit', (event) => {
  event.preventDefault();
  const { email, password } = getFormData(event.currentTarget);
  const user = store.users.find((item) => item.email.toLowerCase() === email.trim().toLowerCase() && item.password === password);
  if (!user) return toast('Invalid email or password.');
  localStorage.setItem(SESSION_KEY, String(user.id));
  event.currentTarget.reset();
  toast('Login successful.');
  loadData();
});

$('registerForm').addEventListener('submit', (event) => {
  event.preventDefault();
  const { name, email, password } = getFormData(event.currentTarget);
  const normalizedEmail = email.trim().toLowerCase();
  if (store.users.some((user) => user.email.toLowerCase() === normalizedEmail)) return toast('That email is already registered.');
  store.users.push({ id: nextId(store.users), name: name.trim(), email: normalizedEmail, password, role: 'user', created_at: timestamp() });
  saveStore();
  event.currentTarget.reset();
  toast('User registered. You can log in now.');
  loadData();
});

$('logoutBtn').addEventListener('click', () => {
  localStorage.removeItem(SESSION_KEY);
  toast('Logged out.');
  loadData();
});

$('refreshBooks').addEventListener('click', loadData);
$('bookSearch').addEventListener('input', renderBooks);

$('booksGrid').addEventListener('click', (event) => {
  const borrowId = Number(event.target.dataset.borrow);
  const edit = event.target.dataset.editBook;
  const deleteBook = Number(event.target.dataset.deleteBook);
  if (borrowId) {
    if (state.user?.role !== 'user') return toast('Sign in with a user account to borrow books.');
    const book = store.books.find((item) => item.id === borrowId);
    if (!book || activeLoanCount(book.id) >= book.total_copies) return toast('This book is not currently available.');
    store.loans.push({ id: nextId(store.loans), user_id: state.user.id, book_id: book.id, borrowed_at: dateString(), due_date: addDays(LOAN_DAYS), returned_at: null });
    saveStore();
    toast(`Book borrowed. Due on ${addDays(LOAN_DAYS)}.`);
    return loadData();
  }
  if (deleteBook && state.user?.role === 'admin') {
    if (activeLoanCount(deleteBook)) return toast('Return all active loans before deleting this book.');
    store.books = store.books.filter((book) => book.id !== deleteBook);
    store.loans = store.loans.filter((loan) => loan.book_id !== deleteBook);
    saveStore();
    toast('Book deleted.');
    return loadData();
  }
  if (edit && state.user?.role === 'admin') {
    const book = JSON.parse(decodeURIComponent(edit));
    const form = $('bookForm');
    Object.entries(book).forEach(([key, value]) => { if (form.elements[key]) form.elements[key].value = value ?? ''; });
  }
});

function returnLoan(loanId) {
  const loan = store.loans.find((item) => item.id === loanId);
  if (!loan || loan.returned_at) return;
  if (state.user?.role !== 'admin' && loan.user_id !== state.user?.id) return toast('You can only return your own books.');
  loan.returned_at = timestamp();
  saveStore();
  toast('Book returned.');
  loadData();
}

$('loansList').addEventListener('click', (event) => returnLoan(Number(event.target.dataset.return)));
$('adminLoansList').addEventListener('click', (event) => returnLoan(Number(event.target.dataset.return)));

$('bookForm').addEventListener('submit', (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const id = Number(data.id);
  const totalCopies = Number(data.total_copies);
  if (!data.title.trim() || !data.author.trim() || !Number.isInteger(totalCopies) || totalCopies < 1) return toast('Enter a title, author, and at least one copy.');
  if (id && totalCopies < activeLoanCount(id)) return toast('Copy count cannot be lower than active loans.');
  const bookData = { title: data.title.trim(), author: data.author.trim(), isbn: data.isbn.trim(), category: data.category.trim(), description: data.description.trim(), total_copies: totalCopies, updated_at: timestamp() };
  if (id) {
    const book = store.books.find((item) => item.id === id);
    if (!book) return toast('Book not found.');
    Object.assign(book, bookData);
  } else {
    store.books.push({ id: nextId(store.books), ...bookData, created_at: timestamp() });
  }
  saveStore();
  event.currentTarget.reset();
  toast('Book saved.');
  loadData();
});

$('userForm').addEventListener('submit', (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const id = Number(data.id);
  const email = data.email.trim().toLowerCase();
  if (!data.name.trim() || !email) return toast('Name and email are required.');
  if (store.users.some((user) => user.email.toLowerCase() === email && user.id !== id)) return toast('That email is already registered.');
  if (!id && !data.password) return toast('A password is required for a new user.');
  if (id) {
    const user = store.users.find((item) => item.id === id);
    if (!user) return toast('User not found.');
    Object.assign(user, { name: data.name.trim(), email, role: data.role === 'admin' ? 'admin' : 'user' });
    if (data.password) user.password = data.password;
  } else {
    store.users.push({ id: nextId(store.users), name: data.name.trim(), email, password: data.password, role: data.role === 'admin' ? 'admin' : 'user', created_at: timestamp() });
  }
  saveStore();
  event.currentTarget.reset();
  toast('User saved.');
  loadData();
});

$('usersList').addEventListener('click', (event) => {
  const edit = event.target.dataset.editUser;
  const deleteUser = Number(event.target.dataset.deleteUser);
  if (deleteUser && state.user?.role === 'admin') {
    if (store.loans.some((loan) => loan.user_id === deleteUser && !loan.returned_at)) return toast('Return all active loans before deleting this user.');
    store.users = store.users.filter((user) => user.id !== deleteUser);
    store.loans = store.loans.filter((loan) => loan.user_id !== deleteUser);
    saveStore();
    toast('User deleted.');
    return loadData();
  }
  if (!edit || state.user?.role !== 'admin') return;
  const user = JSON.parse(decodeURIComponent(edit));
  const form = $('userForm');
  Object.entries(user).forEach(([key, value]) => { if (form.elements[key]) form.elements[key].value = value ?? ''; });
  form.elements.password.value = '';
});

loadData();
