(function () {
    const searchInput = document.getElementById("searchInput");
    const sectorFilter = document.getElementById("sectorFilter");
    const categoryButtons = document.querySelectorAll(".category-chip");
    const productCards = document.querySelectorAll(".product-card");

    const selectedCount = document.getElementById("selectedCount");
    const totalUnits = document.getElementById("totalUnits");
    const totalAmount = document.getElementById("totalAmount");
    const selectedProductsList = document.getElementById("selectedProductsList");
    const submitButton = document.getElementById("submitButton");
    const emptyMessage = document.getElementById("emptyMessage");

    const CART_KEY = "sweetops-cart";

    let activeCategory = "all";

    function normalizeText(value) {
        return String(value || "")
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "");
    }

    function formatCLP(value) {
        return Number(value || 0).toLocaleString("es-CL");
    }

    function debounce(callback, delay = 180) {
        let timeout;

        return function (...args) {
            clearTimeout(timeout);

            timeout = setTimeout(function () {
                callback(...args);
            }, delay);
        };
    }

    function getQuantityInput(card) {
        return card.querySelector(".quantity-input");
    }

    function safeQuantity(value) {
        const quantity = parseInt(value || "0", 10);

        if (Number.isNaN(quantity) || quantity < 0) {
            return 0;
        }

        return quantity;
    }

    function saveCartState() {
        const state = [];

        productCards.forEach(function (card) {
            const input = getQuantityInput(card);
            const quantity = safeQuantity(input.value);

            if (quantity > 0) {
                state.push({
                    name: input.dataset.name,
                    quantity: quantity,
                });
            }
        });

        sessionStorage.setItem(CART_KEY, JSON.stringify(state));
    }

    function restoreCartState() {
        const raw = sessionStorage.getItem(CART_KEY);

        if (!raw) {
            return;
        }

        try {
            const state = JSON.parse(raw);

            state.forEach(function (item) {
                productCards.forEach(function (card) {
                    const input = getQuantityInput(card);

                    if (
                        normalizeText(input.dataset.name) ===
                        normalizeText(item.name)
                    ) {
                        input.value = safeQuantity(item.quantity);
                    }
                });
            });
        } catch (error) {
            console.error("No se pudo restaurar el carrito:", error);
            sessionStorage.removeItem(CART_KEY);
        }
    }

    function animateCard(card) {
        if (!card.animate) {
            return;
        }

        card.animate(
            [
                { transform: "scale(1)" },
                { transform: "scale(1.025)" },
                { transform: "scale(1)" },
            ],
            {
                duration: 160,
                easing: "ease-out",
            }
        );
    }

    function filterProducts() {
        const search = normalizeText(searchInput ? searchInput.value : "");
        const selectedSector = sectorFilter ? sectorFilter.value : "all";

        let visibleCount = 0;

        productCards.forEach(function (card) {
            const name = normalizeText(card.dataset.name);
            const sector = normalizeText(card.dataset.sector);
            const category = normalizeText(card.dataset.category);
            const favorite = card.dataset.favorite === "true";

            const matchesSearch = name.includes(search);
            const matchesSector =
                selectedSector === "all" || sector === selectedSector;

            let matchesCategory = true;

            if (activeCategory === "favorites") {
                matchesCategory = favorite;
            } else if (activeCategory !== "all") {
                matchesCategory = category === activeCategory;
            }

            if (matchesSearch && matchesSector && matchesCategory) {
                card.hidden = false;
                visibleCount += 1;
            } else {
                card.hidden = true;
            }
        });

        if (emptyMessage) {
            emptyMessage.style.display = visibleCount === 0 ? "block" : "none";
        }
    }

    function updateSummary() {
        let selectedProducts = 0;
        let units = 0;
        let total = 0;
        let html = "";

        productCards.forEach(function (card) {
            const input = getQuantityInput(card);
            const quantity = safeQuantity(input.value);
            const price = Number.parseFloat(input.dataset.price || "0");
            const name = input.dataset.name || "Producto";

            input.value = quantity;

            if (quantity > 0) {
                card.classList.add("selected");

                selectedProducts += 1;
                units += quantity;
                total += quantity * price;

                html += `
                    <div class="summary-line">
                        <span>${quantity}x ${name}</span>
                        <strong>$${formatCLP(quantity * price)}</strong>
                    </div>
                `;
            } else {
                card.classList.remove("selected");
            }
        });

        if (selectedCount) {
            selectedCount.textContent = selectedProducts;
        }

        if (totalUnits) {
            totalUnits.textContent = units;
        }

        if (totalAmount) {
            totalAmount.textContent = formatCLP(total);
        }

        if (selectedProductsList) {
            if (selectedProducts === 0) {
                selectedProductsList.innerHTML = `
                    <div class="summary-line">
                        <span>Sin productos</span>
                    </div>
                `;
            } else {
                selectedProductsList.innerHTML = html;
            }
        }

        if (submitButton) {
            if (selectedProducts === 0) {
                submitButton.disabled = true;
                submitButton.textContent = "Selecciona productos";
            } else {
                submitButton.disabled = false;
                submitButton.textContent = `Crear Pedido • $${formatCLP(total)}`;
            }
        }

        saveCartState();
    }

    function addProduct(card, amount) {
        const input = getQuantityInput(card);
        const current = safeQuantity(input.value);
        const next = Math.max(0, current + amount);

        input.value = next;

        animateCard(card);
        updateSummary();
    }

    function clearCart() {
        productCards.forEach(function (card) {
            const input = getQuantityInput(card);
            input.value = 0;
        });

        sessionStorage.removeItem(CART_KEY);
        updateSummary();
    }

    window.clearCart = clearCart;

    productCards.forEach(function (card) {
        const input = getQuantityInput(card);
        const plusBtn = card.querySelector(".plus-btn");
        const minusBtn = card.querySelector(".minus-btn");

        card.addEventListener("click", function (event) {
            const clickedControl =
                event.target.closest(".qty-btn") ||
                event.target.closest(".quantity-input");

            if (clickedControl) {
                return;
            }

            addProduct(card, 1);
        });

        if (plusBtn) {
            plusBtn.addEventListener("click", function (event) {
                event.stopPropagation();
                addProduct(card, 1);
            });
        }

        if (minusBtn) {
            minusBtn.addEventListener("click", function (event) {
                event.stopPropagation();
                addProduct(card, -1);
            });
        }

        if (input) {
            input.addEventListener(
                "input",
                debounce(function () {
                    input.value = safeQuantity(input.value);
                    updateSummary();
                }, 120)
            );
        }
    });

    categoryButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            categoryButtons.forEach(function (btn) {
                btn.classList.remove("active");
            });

            button.classList.add("active");
            activeCategory = button.dataset.category || "all";

            filterProducts();
        });
    });

    if (searchInput) {
        searchInput.addEventListener("input", debounce(filterProducts, 120));
    }

    if (sectorFilter) {
        sectorFilter.addEventListener("change", filterProducts);
    }

    restoreCartState();
    updateSummary();
    filterProducts();
})();