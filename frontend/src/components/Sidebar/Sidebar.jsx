import PageTree from "../PageTree/PageTree"

import "./Sidebar.css"

function Sidebar({

    booklets,

    setSelectedPage,

    setSelectedBooklet,

    selectedPage
}) {

    return (

        <div className="sidebar">

            <div className="sidebar-card">

                <div className="queue-header">

                    Review Queue

                </div>

                <PageTree

                    booklets={booklets}

                    selectedPage={
                        selectedPage
                    }

                    setSelectedPage={
                        setSelectedPage
                    }

                    setSelectedBooklet={
                        setSelectedBooklet
                    }
                />

            </div>
        </div>
    )
}

export default Sidebar