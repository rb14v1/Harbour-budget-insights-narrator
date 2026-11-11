import { apiClient } from "./client";
import type { MonthlyInsightResponse } from "../types";

export function fetchInsight(year: number, month: number) {
  return apiClient.get<MonthlyInsightResponse>(`/insights/${year}/${month}/`);
}

export function generateInsight(year: number, month: number) {
  return apiClient.post<MonthlyInsightResponse>(`/insights/${year}/${month}/generate/`);
}
