# Swag Labs E-Commerce Application – Test Plan

## 1. Introduction
This test plan describes the overall testing approach for the Swag Labs web application (https://www.saucedemo.com) based on the Software Requirements Specification (SRS‑SAUCEDEMO‑2026‑V1.0). It provides traceability from requirements to test cases, defines scope, test strategy, resources, schedule, and risks.

## 2. Scope
- **In‑Scope:** Functional verification of authentication, product catalog, cart management, checkout flow, global navigation, and supporting non‑functional checks (performance, security, accessibility, responsiveness). All user personas listed in the SRS will be exercised where applicable.
- **Out‑of‑Scope:** Backend API unit testing, load‑testing beyond the defined performance glitch user scenario, and visual regression testing beyond the scope of functional automation.

## 3. Test Strategy
| Aspect | Approach |
|--------|----------|
| **Test Levels** | Unit (not covered), Integration (module‑level UI tests), System (end‑to‑end), Acceptance (smoke) |
| **Execution Types** | Manual exploratory validation for newly discovered defects; Automated regression using Playwright/Python or Java (Page Object Model). |
| **Test Types** | Functional, Negative, Boundary, Security, Performance (glitch user), Compatibility (Chrome/Firefox/Safari/Edge), Responsive (375px+), Accessibility (keyboard, labels, contrast). |
| **Automation Scope** | All test cases listed in the **Test Cases** section are automation‑ready (status: `ready_for_generation`). |
| **Data Management** | Use predefined credentials from the SRS. Test data is reset via the **Reset App State** feature before each independent test. |
| **Environment** | Staging URL – https://www.saucedemo.com (public demo). Browsers: latest Chrome, Firefox, Safari, Edge. Mobile device emulation at 375 px width. |

## 4. Test Suite Mapping (Page Object Model)
- `AuthPage` – login, logout, route protection.
- `InventoryPage` – product list, sorting, navigation to detail.
- `ProductDetailPage` – add/remove from cart, back navigation.
- `CartPage` – item list, remove, continue shopping, checkout.
- `CheckoutStepOnePage` – user info form.
- `CheckoutStepTwoPage` – order summary, tax calculation.
- `CheckoutCompletePage` – order confirmation.
- `SideMenu` – navigation links, reset state.

## 5. Traceability Matrix
| Requirement ID | Test Case ID |
|----------------|--------------|
| REQ‑AUTH‑001 | TC‑AUTH‑001 |
| REQ‑AUTH‑002 | TC‑AUTH‑002 |
| REQ‑AUTH‑003 | TC‑AUTH‑003 |
| REQ‑AUTH‑004 | TC‑AUTH‑004 |
| REQ‑AUTH‑005 | TC‑AUTH‑005 |
| REQ‑AUTH‑006 | TC‑AUTH‑006 |
| REQ‑CAT‑001 | TC‑CAT‑001 |
| REQ‑CAT‑002 | TC‑CAT‑002 |
| REQ‑CAT‑003 | TC‑CAT‑003 |
| REQ‑CRT‑001 | TC‑CRT‑001 |
| REQ‑CRT‑002 | TC‑CRT‑002 |
| REQ‑CRT‑003 | TC‑CRT‑003 |
| REQ‑CRT‑004 | TC‑CRT‑004 |
| REQ‑CHK‑001 | TC‑E2E‑001 |
| REQ‑CHK‑002 | TC‑E2E‑002 |
| REQ‑CHK‑003 | TC‑E2E‑003 |
| REQ‑CHK‑004 | TC‑E2E‑004 |
| REQ‑GLB‑001 | TC‑GLB‑001 |
| REQ‑GLB‑002 | TC‑GLB‑002 |

## 6. Assumptions & Evidence Gaps
- The initial exploration captured only the login page layout (username, password fields, login button, and informational text). All other UI elements are assumed to exist as described in the SRS; their presence is not yet verified by exploratory evidence.
- It is assumed that the *Reset App State* link clears local storage and session data.
- Network‑delay behavior for `performance_glitch_user` is assumed to be triggered by the backend mock used by the demo site.

## 7. Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| UI changes not reflected in spec | Medium | Periodic UI inspection; update test cases accordingly. |
| Flaky network causing false performance failures | Low | Use retry logic and timeout thresholds per NFR‑PERF‑001. |
| Cross‑browser rendering differences | Medium | Execute the full suite on all supported browsers. |

## 8. Schedule (high‑level)
- **Week 1‑2:** Test case authoring & review.
- **Week 3‑4:** Automation script development (POM implementation).
- **Week 5:** Cross‑browser and responsive execution.
- **Week 6:** Regression run, defect triage, test plan sign‑off.

---
*Prepared by: Senior QA Test Planner*
*Date: 2026‑10‑28*