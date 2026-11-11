import { apiClient } from "./client";
import type { Category, Paginated } from "../types";

export function listCategories() {
  return apiClient.get<Paginated<Category>>("/categories/", { params: { page_size: 100 } });
}

export function createCategory(name: string) {
  return apiClient.post<Category>("/categories/", { name });
}

export function updateCategory(id: number, name: string) {
  return apiClient.patch<Category>(`/categories/${id}/`, { name });
}

export function deleteCategory(id: number) {
  return apiClient.delete(`/categories/${id}/`);
}
