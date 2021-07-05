document.querySelector('.plotly-graph-div').on('plotly_click', function(event){
    if (event['points'][0]['curveNumber'] != 0) {
      let trace_id = event['points'][0]['curveNumber']
      document.getElementById('alert').style.display = "none"
      document.getElementById("h2").innerHTML = ""
      const card = `<div class="card" id="card">
                        <div class="card_upper">Latitude / Longitude (L72)</div>
                        <div class="card_lower">${event['points'][0].y} / ${event['points'][0].x}</div>
                     </div>`
                  h2.insertAdjacentHTML("beforeend", card)
      let new_data = features[trace_id - 1]
      for (const [key, value] of Object.entries(new_data)) {
                    const card = `<div class="card" id="card">
                                    <div class="card_upper">${key}</div>
                                    <div class="card_lower">${value}</div>
                                  </div>`
                  h2.insertAdjacentHTML("beforeend", card)}
      }
})