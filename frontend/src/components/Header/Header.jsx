import "./Header.css"

function Header({

    booklets = {},

    institutionName =
    "Institution Name",

    connectionStatus =
    "connecting",

    logoUrl = null,

    onSettingsClick,

    theme,

    setTheme
}) {

    const totalBooklets =
        Object.keys(booklets).length

    const totalPages =
        Object.values(booklets)
            .reduce(
                (acc, booklet) =>
                    acc +
                    booklet.pages.length,
                0
            )

    const getStatusClass = () => {

        switch (
        connectionStatus
        ) {

            case "connected":
                return "status-connected"

            case "disconnected":
                return "status-disconnected"

            default:
                return "status-connecting"
        }
    }

    const getStatusText = () => {

        switch (
        connectionStatus
        ) {

            case "connected":
                return "Connected"

            case "disconnected":
                return "Disconnected"

            default:
                return "Connecting"
        }
    }

    return (

        <header className="header">

            <div className="header-left">

                <div className="logo">

                    {
                        logoUrl ? (

                            <img
                                src={logoUrl}
                                alt="University Logo"
                            />

                        ) : (

                            <span>
                                LOGO
                            </span>
                        )
                    }

                </div>

                <div>

                    <div className="institution-name">

                        {institutionName}

                    </div>

                    <div className="dashboard-name">

                        OCR Answer-Script Scanner

                    </div>

                </div>

            </div>

            <div className="header-right">

                <div
                    className={
                        `status-pill ${getStatusClass()}`
                    }
                >

                    <span
                        className="status-dot"
                    />

                    {getStatusText()}

                </div>

                <button

                    className="theme-btn"

                    onClick={() =>

                        setTheme(

                            theme === "light"
                                ? "dark"
                                : "light"
                        )
                    }
                >

                    {

                        theme === "light"

                            ? "🌙"

                            : "☀️"

                    }

                </button>

                <button
                    className="settings-btn"
                    onClick={
                        onSettingsClick
                    }
                >

                    ⚙ Settings

                </button>

            </div>


        </header>
    )
}

export default Header