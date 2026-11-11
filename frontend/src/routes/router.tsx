import { createBrowserRouter, Navigate } from "react-router-dom";

import { ProtectedRoute } from "../auth/ProtectedRoute";
import { CategoriesPage } from "../features/categories/CategoriesPage";
import { InsightsPage } from "../features/insights/InsightsPage";
import { TransactionsPage } from "../features/transactions/TransactionsPage";
import { AppLayout } from "../layouts/AppLayout";
import { LoginPage } from "../pages/LoginPage";
import { RegisterPage } from "../pages/RegisterPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: "/", element: <InsightsPage /> },
          { path: "/categories", element: <CategoriesPage /> },
          { path: "/transactions", element: <TransactionsPage /> },
        ],
      },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
