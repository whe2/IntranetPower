import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_welcome_email(to_email, name, username, password, smtp_user, smtp_pass, is_update=False):
    sender_email = smtp_user
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Bienvenido al Equipo Power Corp." if not is_update else "Actualización de Datos en Power Corp."
    msg['From'] = sender_email
    msg['To'] = to_email

    logo_url = "https://ngfihmioixtfnrmlrlam.supabase.co/storage/v1/object/public/power/descarga-removebg-preview.png"
    
    if not is_update:
        html_content = f"""
        <html>
            <body style="margin:0; padding:0; background-color:#F4F7F6; font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="background-color:#FFFFFF; margin-top:30px; border-radius:12px; overflow:hidden; box-shadow:0 8px 16px rgba(0,0,0,0.1);">
                    <tr>
                        <td align="center" bgcolor="#14213D" style="padding:40px 0 30px 0;">
                            <img src="{logo_url}" alt="Power Corp Logo" width="150" style="display:block; margin-bottom:15px;" />
                            <h1 style="color:#FCA311; margin:0; font-size:24px; letter-spacing:1px;">¡Bienvenido al Equipo Power!</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:40px 30px; color:#111111; font-size:16px; line-height:1.6;">
                            <p>Hola <strong>{name}</strong>,</p>
                            <p>Nos complace darte la bienvenida oficial a <strong>Power Corp</strong>. Tu perfil ha sido creado exitosamente en nuestra plataforma Intranet.</p>
                            <p>A continuación, encontrarás tus credenciales de acceso. Te recomendamos guardarlas en un lugar seguro:</p>
                            <div style="background-color:#FAFAFA; border-left:4px solid #FCA311; padding:15px; margin:25px 0;">
                                <p style="margin:5px 0;"><strong>Usuario:</strong> {username}</p>
                                <p style="margin:5px 0;"><strong>Contraseña:</strong> {password}</p>
                            </div>
                            <p>Estamos emocionados de contar contigo y te deseamos mucho éxito en esta nueva etapa.</p>
                            <p>Atentamente,<br><strong style="color:#14213D;">El equipo de RRHH</strong></p>
                        </td>
                    </tr>
                    <tr>
                        <td bgcolor="#14213D" style="padding:20px; text-align:center; color:#FFFFFF; font-size:12px;">
                            <p style="margin:0;">&copy; 2026 Power Link Corp. Todos los derechos reservados.</p>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """
    else:
        html_content = f"""
        <html>
            <body style="margin:0; padding:0; background-color:#F4F7F6; font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="background-color:#FFFFFF; margin-top:30px; border-radius:12px; overflow:hidden; box-shadow:0 8px 16px rgba(0,0,0,0.1);">
                    <tr>
                        <td align="center" bgcolor="#14213D" style="padding:40px 0 30px 0;">
                            <img src="{logo_url}" alt="Power Corp Logo" width="150" style="display:block; margin-bottom:15px;" />
                            <h1 style="color:#FCA311; margin:0; font-size:24px; letter-spacing:1px;">Actualización de Perfil</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:40px 30px; color:#111111; font-size:16px; line-height:1.6;">
                            <p>Hola <strong>{name}</strong>,</p>
                            <p>Te informamos que tus datos personales y de empleado han sido actualizados exitosamente en nuestra plataforma.</p>
                            <p>Si tienes alguna pregunta sobre estos cambios, por favor contacta al departamento de Recursos Humanos.</p>
                            <p>Atentamente,<br><strong style="color:#14213D;">El equipo de RRHH</strong></p>
                        </td>
                    </tr>
                    <tr>
                        <td bgcolor="#14213D" style="padding:20px; text-align:center; color:#FFFFFF; font-size:12px;">
                            <p style="margin:0;">&copy; 2026 Power Link Corp. Todos los derechos reservados.</p>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

    part2 = MIMEText(html_content, 'html')
    msg.attach(part2)

    try:
        server = smtplib.SMTP('mail.smtp2go.com', 2525)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
