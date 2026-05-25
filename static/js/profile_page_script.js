document.getElementById('profile_form').onchange = (e)=>{
    switch (e.target.name) {
        case 'username':
            document.getElementById('username_show').innerHTML ='@' + e.target.value
            break;
        case 'avatar':
            let files  = e.target.files;
            if (files && files.length) {
                let image = new FileReader()
                image.onload = ()=>{
                    document.getElementById('avatar_show').src = image.result
                }
                image.readAsDataURL(files[0])
            }
            break;
    
        default:
            break;
    }
}

document.getElementById("edit_avatar").onclick=()=>{
    document.getElementById('id_avatar').click()
}