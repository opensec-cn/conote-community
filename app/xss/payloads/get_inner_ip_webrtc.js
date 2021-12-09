/*
*  获取内网IP模块
*/
var RTCPeerConnection = window.webkitRTCPeerConnection || window.mozRTCPeerConnection;

    if (window.RTCIceGatherer || RTCPeerConnection){

        var addrs = Object.create(null);
        addrs["0.0.0.0"] = false;

        // Prefer RTCIceGatherer of simplicity.
        if (window.RTCIceGatherer) {
            var iceGatherer = new RTCIceGatherer({
                "gatherPolicy": "all",
                "iceServers": [ ],
            });
            iceGatherer.onlocalcandidate = function (evt) {
                if (evt.candidate.type) {
                  // There may be multiple IP addresses
                  if (evt.candidate.type == "host") {
                      // The ones marked "host" are local IP addresses
                      processIPs(evt.candidate.ip, 1);
                  };
                }
            };
        } else {
          // Construct RTC peer connection
          var servers = {iceServers:[]};
          var mediaConstraints = {optional:[{googIPv6: true}]};
          var rtc = new RTCPeerConnection(servers, mediaConstraints);
          rtc.createDataChannel('', {reliable:false});

          // Upon an ICE candidate being found
          // Grep the SDP data for IP address data
          rtc.onicecandidate = function (evt) {
              if (evt.candidate){
                // There may be multiple local IP addresses
                grepSDP("a="+evt.candidate.candidate);
              }
          };

          // Create an SDP offer
          rtc.createOffer(function (offerDesc) {
              grepSDP(offerDesc.sdp);
              rtc.setLocalDescription(offerDesc);
          }, function (e) {});
        };

        // Return results
        function processIPs(newAddr, pos) {
            if (newAddr in addrs) return;
            else addrs[newAddr] = true;
            var displayAddrs = Object.keys(addrs).filter(function (k) { return addrs[k]; });

            if(displayAddrs) {
                var data = {}
                data['inner_ip_' + pos] = displayAddrs.join(",")
                co.api.send(data)
            }
        }


        // Retrieve IP addresses from SDP
        function grepSDP(sdp) {
            var hosts = [];
            sdp.split('\r\n').forEach(function (line) { // c.f. http://tools.ietf.org/html/rfc4566#page-39
                if (~line.indexOf("a=candidate")) {     // http://tools.ietf.org/html/rfc4566#section-5.13
                    var parts = line.split(' '),        // http://tools.ietf.org/html/rfc5245#section-15.1
                        addr = parts[4],
                        type = parts[7];
                    if (type === 'host') processIPs(addr, 2);
                } else if (~line.indexOf("c=")) {       // http://tools.ietf.org/html/rfc4566#section-5.7
                    var parts = line.split(' '),
                        addr = parts[2];
                    processIPs(addr, 3);
                }
            });
        }
    }