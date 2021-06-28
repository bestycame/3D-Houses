var updatepage=(ccnid) => {
    fetch('/updateccn/' + ccnid)
    .then(response => response.json())
    .then((data) => {
      if(document.getElementById('h1') === null ||
         document.getElementById('h1') === undefined) {
              window.location.href = `./ccn/${ccnid}`;
      } else {
        document.getElementById('alert').style.display = "none"
        document.getElementById("h1").innerHTML = ""
        document.getElementById("h2").innerHTML = ""
          if (data['found'] == true) {
              h1.insertAdjacentHTML("afterbegin", `
                                    <h1>${data['h1']['Name']}</h1>
                                     <p>${data['h1']['ZIP']}</p>
                                    `)

            for (var i = 0; i < data['order'].length; i++) {
                const card = `  <div class="card" id="card">
                                  <div class="card_upper">${data['order'][i]}</div>
                                  <div class="card_lower">${data['h2'][data['order'][i]]}</div>
                                </div> `
                h2.insertAdjacentHTML("beforeend", card)
            }
          } else {
            document.getElementById('alert').style.display = "block"
          }
      }
    })
  }

document.querySelector('#searchbox').addEventListener('click', (event) => {
  event.preventDefault();
  let ccnid = document.getElementById('searchterm').value
  updatepage(ccnid)
})

document.querySelector('.plotly-graph-div').on('plotly_click', function(event){
    ccnid = event['points'][0]['location']
    updatepage(ccnid)
  })
