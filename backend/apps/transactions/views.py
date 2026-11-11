from rest_framework import permissions, viewsets

from apps.transactions.models import Transaction
from apps.transactions.serializers import TransactionSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Transaction.objects.filter(user=self.request.user).select_related("category")

        month = self.request.query_params.get("month")
        if month:
            try:
                year_str, month_str = month.split("-")
                qs = qs.filter(transaction_date__year=int(year_str), transaction_date__month=int(month_str))
            except (ValueError, AttributeError):
                pass

        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category_id=category)

        txn_type = self.request.query_params.get("transaction_type")
        if txn_type:
            qs = qs.filter(transaction_type=txn_type)

        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
