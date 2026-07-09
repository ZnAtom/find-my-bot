#!/bin/bash
POD="foundit-backend-dd868c68-87nqb"
echo "Waiting for pod to become Running..."
while true; do
  STATUS=$(kubectl get pod $POD -o jsonpath='{.status.phase}')
  if [ "$STATUS" = "Running" ]; then
    echo "Pod is Running!"
    break
  fi
  sleep 10
done

echo "Waiting for pod to become Ready (FastAPI started)..."
kubectl wait --for=condition=Ready pod/$POD --timeout=1800s

echo "Testing the POST endpoint..."
IP=$(kubectl get pod $POD -o jsonpath='{.status.podIP}')
curl -s -X POST http://$IP:8000/api/lost-items \
  -H "Content-Type: application/json" \
  -d '{"item_name":"Test Item","description":"Testing submission","location":"Test location","contact_person":"Test person"}' > result.json

cat result.json
echo "Done!"
