
paypal.Buttons({
  createOrder: function(data, actions) {
    return actions.order.create({
      purchase_units: [{
        description: "Hospital Appointment",
        amount: { value: '10.00' }
      }]
    });
  },

  onApprove: function(data, actions) {
    return actions.order.capture().then(function(details) {
      console.log('Payment details:', details);

      // Send appointment + payment details to Django
      fetch("{% url 'appointment_store' %}", {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': '{{ csrf_token }}'
        },
        body: JSON.stringify({
          doctor_id: document.querySelector('select[name="doctors"]').value,
          date: document.querySelector('input[name="date"]').value,
          time: document.querySelector('select[name="time"]').value,
          payment_id: details.id,
          payer_name: details.payer.name.given_name + ' ' + details.payer.name.surname,
          payer_email: details.payer.email_address,
          payment_amount: details.purchase_units[0].payments.captures[0].amount.value,
          payment_currency: details.purchase_units[0].payments.captures[0].amount.currency_code,
          payment_details: details
        })
      })
      .then(res => res.json())
      .then(data => {
        if(data.success){
          alert('Appointment booked successfully!');
          window.location.reload();
        } else {
          alert('' + data.error);
        }
      })
      .catch(err => console.error(err));
    });
  },

  onError: function(err) {
    console.error(err);
    alert("Payment failed or cancelled. Please try again.");
  }
}).render('#paypal-button-container');

