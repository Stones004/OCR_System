import "./Footer.css"

function Footer({

    health,

    websocketStatus

}) {

    const services = [

        {
            label: "api",
            healthy:
                health?.api?.status === "healthy"
        },

        {
            label: "redis",
            healthy:
                health?.redis?.status === "healthy"
        },

        {
            label: "WebSocket",
            healthy:
                websocketStatus ===
                "connected"
        },

        {
            // Data key stays "gpu_worker" (matches the backend health
            // response -- see app/services/gpu_service.py's docstring
            // for why); label is just the display text.
            label: "OCR worker",
            healthy:
                health?.gpu_worker?.status === "healthy"
        },

        {
            label: "telemetry",
            healthy:
                health?.telemetry?.status === "healthy"
        }
    ]

    return (

        <div className="footer">

            <div className="footer-status">

                {

                    services.map(

                        service => (

                            <span

                                key={
                                    service.label
                                }

                                className="footer-status-pill"
                            >

                                <span

                                    className={

                                        service.healthy

                                            ?

                                            "footer-status-dot healthy"

                                            :

                                            "footer-status-dot unhealthy"
                                    }
                                />

                                {
                                    service.label
                                }

                            </span>
                        )
                    )
                }

            </div>

        </div>
    )
}

export default Footer